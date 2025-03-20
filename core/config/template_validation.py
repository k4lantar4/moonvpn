"""
Template validation service.

This module provides validation logic for recovery templates and their parameters.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from app.core.schemas.template import ValidationRule

class ValidationError(Exception):
    """Exception raised when validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class TemplateValidator:
    """Service for validating template parameters against validation rules."""

    @staticmethod
    def validate_required(value: Any, rule: ValidationRule) -> None:
        """Validate required field."""
        if not value:
            raise ValidationError(rule.field, rule.message)

    @staticmethod
    def validate_min(value: Any, rule: ValidationRule) -> None:
        """Validate minimum value."""
        try:
            min_value = float(rule.value)
            if float(value) < min_value:
                raise ValidationError(rule.field, rule.message)
        except (ValueError, TypeError):
            raise ValidationError(rule.field, f"Invalid value for min validation: {value}")

    @staticmethod
    def validate_max(value: Any, rule: ValidationRule) -> None:
        """Validate maximum value."""
        try:
            max_value = float(rule.value)
            if float(value) > max_value:
                raise ValidationError(rule.field, rule.message)
        except (ValueError, TypeError):
            raise ValidationError(rule.field, f"Invalid value for max validation: {value}")

    @staticmethod
    def validate_pattern(value: Any, rule: ValidationRule) -> None:
        """Validate pattern match."""
        try:
            if not re.match(rule.value, str(value)):
                raise ValidationError(rule.field, rule.message)
        except re.error:
            raise ValidationError(rule.field, f"Invalid pattern: {rule.value}")

    @staticmethod
    def validate_custom(value: Any, rule: ValidationRule) -> None:
        """Validate using custom validation function."""
        try:
            # Import the custom validation function
            module_path, func_name = rule.value.split(":")
            module = __import__(module_path, fromlist=[func_name])
            validation_func = getattr(module, func_name)
            
            if not validation_func(value):
                raise ValidationError(rule.field, rule.message)
        except (ImportError, AttributeError) as e:
            raise ValidationError(rule.field, f"Invalid custom validation: {str(e)}")

    @classmethod
    def validate_parameter(cls, value: Any, rules: List[ValidationRule]) -> None:
        """Validate a parameter against all applicable rules."""
        for rule in rules:
            if not rule.is_active:
                continue

            validation_method = getattr(cls, f"validate_{rule.type}", None)
            if validation_method:
                validation_method(value, rule)
            else:
                raise ValidationError(rule.field, f"Unknown validation type: {rule.type}")

    @classmethod
    def validate_template(cls, parameters: Dict[str, Any], rules: List[ValidationRule]) -> Dict[str, str]:
        """Validate all template parameters against their validation rules."""
        errors: Dict[str, str] = {}
        
        # Group rules by field
        field_rules: Dict[str, List[ValidationRule]] = {}
        for rule in rules:
            if rule.is_active:
                field_rules.setdefault(rule.field, []).append(rule)

        # Validate each parameter
        for field, value in parameters.items():
            if field in field_rules:
                try:
                    cls.validate_parameter(value, field_rules[field])
                except ValidationError as e:
                    errors[e.field] = e.message

        return errors

    @classmethod
    def validate_template_data(cls, template_data: Dict[str, Any], rules: List[ValidationRule]) -> bool:
        """Validate template data and return True if valid, False otherwise."""
        errors = cls.validate_template(template_data, rules)
        return len(errors) == 0 