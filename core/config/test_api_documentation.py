import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.api.docs import generate_api_docs

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def api_docs():
    """Generate API documentation."""
    return generate_api_docs()

def test_api_docs_generation(api_docs):
    """Test API documentation generation."""
    # Test OpenAPI schema
    assert "openapi" in api_docs
    assert api_docs["openapi"].startswith("3.")
    
    # Test info section
    assert "info" in api_docs
    assert "title" in api_docs["info"]
    assert "version" in api_docs["info"]
    assert "description" in api_docs["info"]
    
    # Test paths section
    assert "paths" in api_docs
    assert len(api_docs["paths"]) > 0
    
    # Test components section
    assert "components" in api_docs
    assert "schemas" in api_docs["components"]
    assert "securitySchemes" in api_docs["components"]

def test_endpoint_documentation(client, api_docs):
    """Test endpoint documentation."""
    # Test user endpoints
    assert "/api/v1/users" in api_docs["paths"]
    assert "/api/v1/users/{user_id}" in api_docs["paths"]
    
    # Test order endpoints
    assert "/api/v1/orders" in api_docs["paths"]
    assert "/api/v1/orders/{order_id}" in api_docs["paths"]
    
    # Test payment endpoints
    assert "/api/v1/payments" in api_docs["paths"]
    assert "/api/v1/payments/{payment_id}" in api_docs["paths"]
    
    # Test VPN endpoints
    assert "/api/v1/vpn/config" in api_docs["paths"]
    assert "/api/v1/vpn/status" in api_docs["paths"]

def test_request_body_documentation(api_docs):
    """Test request body documentation."""
    # Test user creation request body
    user_path = api_docs["paths"]["/api/v1/users"]
    assert "post" in user_path
    assert "requestBody" in user_path["post"]
    assert "content" in user_path["post"]["requestBody"]
    assert "application/json" in user_path["post"]["requestBody"]["content"]
    
    # Test order creation request body
    order_path = api_docs["paths"]["/api/v1/orders"]
    assert "post" in order_path
    assert "requestBody" in order_path["post"]
    assert "content" in order_path["post"]["requestBody"]
    assert "application/json" in order_path["post"]["requestBody"]["content"]

def test_response_documentation(api_docs):
    """Test response documentation."""
    # Test user response
    user_path = api_docs["paths"]["/api/v1/users/{user_id}"]
    assert "get" in user_path
    assert "responses" in user_path["get"]
    assert "200" in user_path["get"]["responses"]
    assert "404" in user_path["get"]["responses"]
    
    # Test order response
    order_path = api_docs["paths"]["/api/v1/orders/{order_id}"]
    assert "get" in order_path
    assert "responses" in order_path["get"]
    assert "200" in order_path["get"]["responses"]
    assert "404" in order_path["get"]["responses"]

def test_parameter_documentation(api_docs):
    """Test parameter documentation."""
    # Test path parameters
    user_path = api_docs["paths"]["/api/v1/users/{user_id}"]
    assert "parameters" in user_path["get"]
    assert user_path["get"]["parameters"][0]["name"] == "user_id"
    assert user_path["get"]["parameters"][0]["in"] == "path"
    assert user_path["get"]["parameters"][0]["required"] is True
    
    # Test query parameters
    users_path = api_docs["paths"]["/api/v1/users"]
    assert "parameters" in users_path["get"]
    assert any(param["name"] == "skip" for param in users_path["get"]["parameters"])
    assert any(param["name"] == "limit" for param in users_path["get"]["parameters"])

def test_security_documentation(api_docs):
    """Test security documentation."""
    # Test security schemes
    assert "securitySchemes" in api_docs["components"]
    assert "bearerAuth" in api_docs["components"]["securitySchemes"]
    
    # Test security requirements
    for path in api_docs["paths"].values():
        for method in path.values():
            if "security" in method:
                assert method["security"] == [{"bearerAuth": []}]

def test_schema_documentation(api_docs):
    """Test schema documentation."""
    # Test user schema
    assert "User" in api_docs["components"]["schemas"]
    user_schema = api_docs["components"]["schemas"]["User"]
    assert "properties" in user_schema
    assert "id" in user_schema["properties"]
    assert "username" in user_schema["properties"]
    assert "email" in user_schema["properties"]
    
    # Test order schema
    assert "Order" in api_docs["components"]["schemas"]
    order_schema = api_docs["components"]["schemas"]["Order"]
    assert "properties" in order_schema
    assert "id" in order_schema["properties"]
    assert "amount" in order_schema["properties"]
    assert "status" in order_schema["properties"]

def test_example_documentation(api_docs):
    """Test example documentation."""
    # Test user creation example
    user_path = api_docs["paths"]["/api/v1/users"]
    assert "examples" in user_path["post"]["requestBody"]["content"]["application/json"]
    
    # Test order creation example
    order_path = api_docs["paths"]["/api/v1/orders"]
    assert "examples" in order_path["post"]["requestBody"]["content"]["application/json"]

def test_error_documentation(api_docs):
    """Test error documentation."""
    # Test common error responses
    for path in api_docs["paths"].values():
        for method in path.values():
            if "responses" in method:
                assert "400" in method["responses"]
                assert "401" in method["responses"]
                assert "403" in method["responses"]
                assert "404" in method["responses"]
                assert "500" in method["responses"]

def test_documentation_endpoints(client):
    """Test documentation endpoints."""
    # Test OpenAPI JSON endpoint
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    
    # Test ReDoc endpoint
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Test Swagger UI endpoint
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"] 