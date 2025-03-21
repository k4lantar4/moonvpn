"""
Performance testing service for MoonVPN.
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..database.session import SessionLocal
from ..models.performance import PerformanceTest, TestResult
from ..schemas.performance import TestConfig, TestResultCreate

logger = logging.getLogger(__name__)

class PerformanceTestingService:
    """Service for conducting performance tests."""
    
    def __init__(self, db: SessionLocal):
        self.db = db
        self.active_tests: Dict[str, asyncio.Task] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        
    async def start_load_test(self, config: TestConfig) -> str:
        """Start a load test with the given configuration."""
        test_id = f"load_test_{int(time.time())}"
        task = asyncio.create_task(self._run_load_test(test_id, config))
        self.active_tests[test_id] = task
        return test_id
        
    async def start_stress_test(self, config: TestConfig) -> str:
        """Start a stress test with the given configuration."""
        test_id = f"stress_test_{int(time.time())}"
        task = asyncio.create_task(self._run_stress_test(test_id, config))
        self.active_tests[test_id] = task
        return test_id
        
    async def start_scalability_test(self, config: TestConfig) -> str:
        """Start a scalability test with the given configuration."""
        test_id = f"scalability_test_{int(time.time())}"
        task = asyncio.create_task(self._run_scalability_test(test_id, config))
        self.active_tests[test_id] = task
        return test_id
        
    async def stop_test(self, test_id: str) -> bool:
        """Stop a running test."""
        if test_id in self.active_tests:
            task = self.active_tests[test_id]
            task.cancel()
            del self.active_tests[test_id]
            return True
        return False
        
    async def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a test."""
        if test_id in self.active_tests:
            task = self.active_tests[test_id]
            return {
                "test_id": test_id,
                "status": "running" if not task.done() else "completed",
                "results": self.test_results.get(test_id, [])
            }
        return None
        
    async def _run_load_test(self, test_id: str, config: TestConfig):
        """Run a load test."""
        try:
            logger.info(f"Starting load test {test_id}")
            start_time = time.time()
            
            # Create test record
            test = PerformanceTest(
                id=test_id,
                type="load",
                config=config.dict(),
                start_time=datetime.utcnow()
            )
            self.db.add(test)
            self.db.commit()
            
            # Initialize test results
            self.test_results[test_id] = []
            
            # Simulate concurrent users
            tasks = []
            for i in range(config.concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user(test_id, config, i)
                )
                tasks.append(task)
                
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Calculate final metrics
            end_time = time.time()
            duration = end_time - start_time
            
            # Update test record
            test.end_time = datetime.utcnow()
            test.duration = duration
            test.status = "completed"
            self.db.commit()
            
            logger.info(f"Load test {test_id} completed")
            
        except Exception as e:
            logger.error(f"Error in load test {test_id}: {str(e)}")
            if test_id in self.active_tests:
                del self.active_tests[test_id]
                
    async def _run_stress_test(self, test_id: str, config: TestConfig):
        """Run a stress test."""
        try:
            logger.info(f"Starting stress test {test_id}")
            start_time = time.time()
            
            # Create test record
            test = PerformanceTest(
                id=test_id,
                type="stress",
                config=config.dict(),
                start_time=datetime.utcnow()
            )
            self.db.add(test)
            self.db.commit()
            
            # Initialize test results
            self.test_results[test_id] = []
            
            # Gradually increase load until system breaks
            current_users = config.concurrent_users
            while True:
                # Simulate users
                tasks = []
                for i in range(current_users):
                    task = asyncio.create_task(
                        self._simulate_user(test_id, config, i)
                    )
                    tasks.append(task)
                    
                # Wait for tasks to complete
                await asyncio.gather(*tasks)
                
                # Check system health
                if not await self._check_system_health():
                    break
                    
                # Increase load
                current_users *= 2
                
            # Calculate final metrics
            end_time = time.time()
            duration = end_time - start_time
            
            # Update test record
            test.end_time = datetime.utcnow()
            test.duration = duration
            test.status = "completed"
            self.db.commit()
            
            logger.info(f"Stress test {test_id} completed")
            
        except Exception as e:
            logger.error(f"Error in stress test {test_id}: {str(e)}")
            if test_id in self.active_tests:
                del self.active_tests[test_id]
                
    async def _run_scalability_test(self, test_id: str, config: TestConfig):
        """Run a scalability test."""
        try:
            logger.info(f"Starting scalability test {test_id}")
            start_time = time.time()
            
            # Create test record
            test = PerformanceTest(
                id=test_id,
                type="scalability",
                config=config.dict(),
                start_time=datetime.utcnow()
            )
            self.db.add(test)
            self.db.commit()
            
            # Initialize test results
            self.test_results[test_id] = []
            
            # Test horizontal scaling
            for num_instances in range(1, config.max_instances + 1):
                # Simulate users
                tasks = []
                for i in range(config.concurrent_users):
                    task = asyncio.create_task(
                        self._simulate_user(test_id, config, i)
                    )
                    tasks.append(task)
                    
                # Wait for tasks to complete
                await asyncio.gather(*tasks)
                
                # Record metrics for this instance count
                await self._record_scalability_metrics(test_id, num_instances)
                
            # Calculate final metrics
            end_time = time.time()
            duration = end_time - start_time
            
            # Update test record
            test.end_time = datetime.utcnow()
            test.duration = duration
            test.status = "completed"
            self.db.commit()
            
            logger.info(f"Scalability test {test_id} completed")
            
        except Exception as e:
            logger.error(f"Error in scalability test {test_id}: {str(e)}")
            if test_id in self.active_tests:
                del self.active_tests[test_id]
                
    async def _simulate_user(self, test_id: str, config: TestConfig, user_id: int):
        """Simulate a user's actions."""
        try:
            start_time = time.time()
            
            # Simulate user actions
            for _ in range(config.actions_per_user):
                # Record resource usage
                await self._record_resource_usage(test_id, user_id)
                
                # Simulate API calls
                await self._simulate_api_calls(config)
                
                # Wait between actions
                await asyncio.sleep(config.action_delay)
                
            end_time = time.time()
            duration = end_time - start_time
            
            # Record test result
            result = TestResultCreate(
                test_id=test_id,
                user_id=user_id,
                duration=duration,
                success=True
            )
            self.test_results[test_id].append(result)
            
        except Exception as e:
            logger.error(f"Error simulating user {user_id} in test {test_id}: {str(e)}")
            
    async def _record_resource_usage(self, test_id: str, user_id: int):
        """Record system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            result = TestResultCreate(
                test_id=test_id,
                user_id=user_id,
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_usage=disk_usage,
                timestamp=datetime.utcnow()
            )
            self.test_results[test_id].append(result)
            
        except Exception as e:
            logger.error(f"Error recording resource usage: {str(e)}")
            
    async def _simulate_api_calls(self, config: TestConfig):
        """Simulate API calls."""
        try:
            # Simulate API latency
            await asyncio.sleep(config.api_latency)
            
            # Simulate API errors
            if config.error_rate > 0 and random.random() < config.error_rate:
                raise Exception("Simulated API error")
                
        except Exception as e:
            logger.error(f"Error simulating API calls: {str(e)}")
            
    async def _check_system_health(self) -> bool:
        """Check if the system is healthy."""
        try:
            # Check CPU usage
            if psutil.cpu_percent() > 90:
                return False
                
            # Check memory usage
            if psutil.virtual_memory().percent > 90:
                return False
                
            # Check disk usage
            if psutil.disk_usage('/').percent > 90:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return False
            
    async def _record_scalability_metrics(self, test_id: str, num_instances: int):
        """Record scalability metrics."""
        try:
            # Record metrics for this instance count
            result = TestResultCreate(
                test_id=test_id,
                num_instances=num_instances,
                cpu_usage=psutil.cpu_percent(),
                memory_usage=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent,
                timestamp=datetime.utcnow()
            )
            self.test_results[test_id].append(result)
            
        except Exception as e:
            logger.error(f"Error recording scalability metrics: {str(e)}")
            
    async def shutdown(self):
        """Shutdown the performance testing service."""
        # Cancel all active tests
        for test_id in list(self.active_tests.keys()):
            await self.stop_test(test_id)
            
        # Clear test results
        self.test_results.clear() 