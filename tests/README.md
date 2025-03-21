# MoonVPN Test Suite

This directory contains the test suite for the MoonVPN application. The tests are organized into several categories:

- `conftest.py`: Common test fixtures and configuration
- `base.py`: Base test class with shared functionality
- `constants.py`: Test constants and data templates
- `helpers.py`: Helper functions for common test operations
- `markers.py`: Custom pytest markers
- `utils.py`: Utility functions for testing
- `config.py`: Test-specific configuration settings

## Test Structure

```
tests/
├── conftest.py          # Common test fixtures
├── base.py             # Base test class
├── constants.py        # Test constants
├── helpers.py          # Helper functions
├── markers.py          # Custom pytest markers
├── utils.py            # Utility functions
├── config.py           # Test configuration
├── unit/               # Unit tests
├── integration/        # Integration tests
├── performance/        # Performance tests
└── api/               # API tests
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Set up environment variables:
```bash
cp .env.example .env.test
# Edit .env.test with your test settings
```

### Running All Tests

```bash
pytest
```

### Running Specific Test Categories

```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run performance tests only
pytest tests/performance/

# Run API tests only
pytest tests/api/
```

### Running Tests with Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html

# View coverage report
open coverage_html/index.html
```

## Test Categories

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Fast execution
- Located in `tests/unit/`

### Integration Tests

- Test component interactions
- Use test database
- Slower execution
- Located in `tests/integration/`

### Performance Tests

- Test system under load
- Measure response times
- Located in `tests/performance/`

### API Tests

- Test API endpoints
- Use test client
- Located in `tests/api/`

## Writing Tests

### Using the Base Test Class

```python
from tests.base import TestBase

class TestUserAPI(TestBase):
    async def test_create_user(self, db, client):
        # Test code here
        pass
```

### Using Test Fixtures

```python
async def test_vpn_config(self, db, test_user, client):
    # Test code here
    pass
```

### Using Test Helpers

```python
async def test_payment(self, db, test_user):
    payment = await self.create_test_payment(db, test_user.id)
    # Test code here
```

## Best Practices

1. Use descriptive test names
2. Keep tests independent
3. Use fixtures for common setup
4. Clean up after tests
5. Mock external services
6. Use appropriate assertions
7. Follow AAA pattern (Arrange, Act, Assert)

## Continuous Integration

Tests are automatically run in CI/CD pipeline:

1. Install dependencies
2. Set up test environment
3. Run tests with coverage
4. Upload coverage report
5. Check test results

## Troubleshooting

### Common Issues

1. Database connection errors:
   - Check database URL in `.env.test`
   - Ensure database is running
   - Check database permissions

2. Test timeout errors:
   - Increase timeout in test settings
   - Check for long-running operations
   - Use appropriate async/await patterns

3. Coverage report issues:
   - Check coverage configuration
   - Ensure all files are included
   - Check for excluded patterns

### Debugging Tips

1. Use `pytest -v` for verbose output
2. Use `pytest -s` to see print statements
3. Use `pytest --pdb` for post-mortem debugging
4. Use `pytest -x` to stop on first failure
5. Use `pytest --trace` for detailed traceback

## Contributing

1. Write tests for new features
2. Update existing tests when modifying code
3. Ensure all tests pass before submitting PR
4. Add appropriate test documentation
5. Follow test naming conventions 