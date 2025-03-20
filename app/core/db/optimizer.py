from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import select, text
from sqlalchemy.orm import Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import cache

T = TypeVar('T')

class QueryOptimizer:
    """Database query optimizer with caching and performance monitoring."""
    
    def __init__(self, session: AsyncSession):
        """Initialize query optimizer with session."""
        self.session = session
        self._query_stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
        
    async def get_or_create(
        self,
        model: Type[T],
        cache_key: str,
        query: Query,
        create_func: callable,
        cache_ttl: int = 300
    ) -> T:
        """Get from cache or database, create if not exists."""
        # Try cache first
        cached = await cache.get(cache_key)
        if cached:
            self._query_stats["hits"] += 1
            return model(**cached)
            
        # Try database
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        
        if instance:
            self._query_stats["hits"] += 1
            await cache.set(cache_key, instance.__dict__, expire=cache_ttl)
            return instance
            
        # Create new instance
        try:
            instance = await create_func()
            self._query_stats["hits"] += 1
            await cache.set(cache_key, instance.__dict__, expire=cache_ttl)
            return instance
        except Exception as e:
            self._query_stats["errors"] += 1
            raise
            
    async def get_many(
        self,
        model: Type[T],
        cache_key: str,
        query: Query,
        cache_ttl: int = 300
    ) -> List[T]:
        """Get multiple instances with caching."""
        # Try cache first
        cached = await cache.get(cache_key)
        if cached:
            self._query_stats["hits"] += 1
            return [model(**item) for item in cached]
            
        # Try database
        result = await self.session.execute(query)
        instances = result.scalars().all()
        
        if instances:
            self._query_stats["hits"] += 1
            await cache.set(
                cache_key,
                [instance.__dict__ for instance in instances],
                expire=cache_ttl
            )
            return instances
            
        self._query_stats["misses"] += 1
        return []
        
    async def bulk_create(
        self,
        model: Type[T],
        items: List[Dict[str, Any]],
        cache_key_prefix: str,
        cache_ttl: int = 300
    ) -> List[T]:
        """Bulk create instances with caching."""
        try:
            # Create instances
            instances = [model(**item) for item in items]
            self.session.add_all(instances)
            await self.session.commit()
            
            # Cache instances
            for instance in instances:
                cache_key = f"{cache_key_prefix}:{instance.id}"
                await cache.set(cache_key, instance.__dict__, expire=cache_ttl)
                
            self._query_stats["hits"] += 1
            return instances
        except Exception as e:
            self._query_stats["errors"] += 1
            await self.session.rollback()
            raise
            
    async def bulk_update(
        self,
        model: Type[T],
        items: List[Dict[str, Any]],
        cache_key_prefix: str,
        cache_ttl: int = 300
    ) -> List[T]:
        """Bulk update instances with cache invalidation."""
        try:
            # Update instances
            for item in items:
                instance = await self.session.get(model, item["id"])
                if instance:
                    for key, value in item.items():
                        if key != "id":
                            setattr(instance, key, value)
                            
            await self.session.commit()
            
            # Update cache
            for item in items:
                cache_key = f"{cache_key_prefix}:{item['id']}"
                await cache.set(cache_key, item, expire=cache_ttl)
                
            self._query_stats["hits"] += 1
            return [await self.session.get(model, item["id"]) for item in items]
        except Exception as e:
            self._query_stats["errors"] += 1
            await self.session.rollback()
            raise
            
    async def bulk_delete(
        self,
        model: Type[T],
        ids: List[int],
        cache_key_prefix: str
    ) -> int:
        """Bulk delete instances with cache invalidation."""
        try:
            # Delete instances
            result = await self.session.execute(
                text(f"DELETE FROM {model.__tablename__} WHERE id = ANY(:ids)"),
                {"ids": ids}
            )
            await self.session.commit()
            
            # Invalidate cache
            for id in ids:
                cache_key = f"{cache_key_prefix}:{id}"
                await cache.delete(cache_key)
                
            self._query_stats["hits"] += 1
            return result.rowcount
        except Exception as e:
            self._query_stats["errors"] += 1
            await self.session.rollback()
            raise
            
    async def get_stats(self) -> Dict[str, int]:
        """Get query statistics."""
        return self._query_stats.copy()
        
    async def clear_stats(self) -> None:
        """Clear query statistics."""
        self._query_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
        
    async def analyze_query(self, query: Query) -> Dict[str, Any]:
        """Analyze query performance."""
        try:
            # Get query plan
            plan = await self.session.execute(
                text(f"EXPLAIN ANALYZE {query.statement}")
            )
            return {
                "plan": plan.fetchall(),
                "stats": self._query_stats.copy()
            }
        except Exception as e:
            self._query_stats["errors"] += 1
            return {
                "error": str(e),
                "stats": self._query_stats.copy()
            } 