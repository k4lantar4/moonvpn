"""
Template testing service for system health monitoring.

This module provides functionality for testing recovery action templates
in a controlled environment.
"""

import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.core.models.template import RecoveryTemplate
from app.core.models.template_test import TemplateTestResult
from app.core.schemas.template_test import TemplateTestCreate, TemplateTestResult as TemplateTestResultSchema

class TemplateTestService:
    """Service for testing recovery action templates."""

    def __init__(self, db: Session):
        """Initialize the template test service.
        
        Args:
            db: Database session
        """
        self.db = db

    def run_test(
        self,
        template_id: int,
        parameters: Dict[str, Any]
    ) -> Optional[TemplateTestResultSchema]:
        """Run a test for a recovery template.
        
        Args:
            template_id: ID of the template to test
            parameters: Test parameters
            
        Returns:
            Optional[TemplateTestResultSchema]: Test result if successful
        """
        try:
            # Get template
            template = self.db.query(RecoveryTemplate).filter(
                RecoveryTemplate.id == template_id
            ).first()
            
            if not template:
                return None

            # Start timing
            start_time = time.time()

            # Validate parameters
            validation_result = self._validate_parameters(template, parameters)
            if not validation_result['is_valid']:
                return self._create_test_result(
                    template_id=template_id,
                    status='failure',
                    message='Parameter validation failed',
                    execution_time=time.time() - start_time,
                    parameters=parameters,
                    errors=validation_result['errors']
                )

            # Simulate strategy execution
            execution_result = self._simulate_strategy_execution(template, parameters)
            
            # Create test result
            return self._create_test_result(
                template_id=template_id,
                status=execution_result['status'],
                message=execution_result['message'],
                execution_time=time.time() - start_time,
                parameters=parameters,
                errors=execution_result.get('errors')
            )

        except Exception as e:
            return self._create_test_result(
                template_id=template_id,
                status='error',
                message=str(e),
                execution_time=time.time() - start_time,
                parameters=parameters
            )

    def get_test_results(
        self,
        template_id: int,
        limit: int = 10
    ) -> List[TemplateTestResultSchema]:
        """Get test results for a template.
        
        Args:
            template_id: ID of the template
            limit: Maximum number of results to return
            
        Returns:
            List[TemplateTestResultSchema]: List of test results
        """
        results = self.db.query(TemplateTestResult).filter(
            TemplateTestResult.template_id == template_id
        ).order_by(
            TemplateTestResult.created_at.desc()
        ).limit(limit).all()
        
        return [TemplateTestResultSchema.from_orm(result) for result in results]

    def _validate_parameters(
        self,
        template: RecoveryTemplate,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate template parameters.
        
        Args:
            template: Template to validate
            parameters: Parameters to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        errors = {}
        
        # Check required parameters
        for key, value in template.parameters.items():
            if key not in parameters:
                errors[key] = 'Required parameter missing'
            elif not parameters[key]:
                errors[key] = 'Parameter value cannot be empty'
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _simulate_strategy_execution(
        self,
        template: RecoveryTemplate,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate strategy execution.
        
        Args:
            template: Template to simulate
            parameters: Test parameters
            
        Returns:
            Dict[str, Any]: Simulation result
        """
        try:
            # Simulate different strategies
            if template.strategy == 'service_restart':
                return self._simulate_service_restart(parameters)
            elif template.strategy == 'cache_clear':
                return self._simulate_cache_clear(parameters)
            elif template.strategy == 'connection_reset':
                return self._simulate_connection_reset(parameters)
            elif template.strategy == 'resource_scaling':
                return self._simulate_resource_scaling(parameters)
            elif template.strategy == 'failover':
                return self._simulate_failover(parameters)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown strategy: {template.strategy}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def _simulate_service_restart(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate service restart strategy."""
        return {
            'status': 'success',
            'message': 'Service restart simulation completed successfully'
        }

    def _simulate_cache_clear(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate cache clear strategy."""
        return {
            'status': 'success',
            'message': 'Cache clear simulation completed successfully'
        }

    def _simulate_connection_reset(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate connection reset strategy."""
        return {
            'status': 'success',
            'message': 'Connection reset simulation completed successfully'
        }

    def _simulate_resource_scaling(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate resource scaling strategy."""
        return {
            'status': 'success',
            'message': 'Resource scaling simulation completed successfully'
        }

    def _simulate_failover(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate failover strategy."""
        return {
            'status': 'success',
            'message': 'Failover simulation completed successfully'
        }

    def _create_test_result(
        self,
        template_id: int,
        status: str,
        message: str,
        execution_time: float,
        parameters: Dict[str, Any],
        errors: Optional[Dict[str, str]] = None
    ) -> TemplateTestResultSchema:
        """Create a test result record.
        
        Args:
            template_id: ID of the template
            status: Test status
            message: Test message
            execution_time: Execution time in seconds
            parameters: Test parameters
            errors: Optional validation errors
            
        Returns:
            TemplateTestResultSchema: Created test result
        """
        test_result = TemplateTestResult(
            template_id=template_id,
            status=status,
            message=message,
            execution_time=execution_time,
            parameters=parameters,
            errors=errors
        )
        
        self.db.add(test_result)
        self.db.commit()
        self.db.refresh(test_result)
        
        return TemplateTestResultSchema.from_orm(test_result) 