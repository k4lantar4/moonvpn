from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.server import Server
from app.schemas.server import ServerCreate, ServerUpdate # Schemas need to be created
from app.crud.base import CRUDBase

class CRUDServer(CRUDBase[Server, ServerCreate, ServerUpdate]):
    def get_by_ip_address(self, db: Session, *, ip_address: str) -> Optional[Server]:
        """ Retrieves a server by its unique IP address. """
        return db.query(self.model).filter(self.model.ip_address == ip_address).first()

    def get_by_hostname(self, db: Session, *, hostname: str) -> Optional[Server]:
        """ Retrieves a server by its unique hostname (if set). """
        return db.query(self.model).filter(self.model.hostname == hostname).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False
    ) -> List[Server]:
        query = db.query(self.model)
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.offset(skip).limit(limit).all()

    # Add other server-specific methods if needed

# Create a singleton instance
server = CRUDServer(Server) 