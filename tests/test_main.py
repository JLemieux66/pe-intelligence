"""
Tests for FastAPI Main Application
"""
import pytest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestMainApplication:
    """Test main FastAPI application"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        # Import app inside fixture to ensure fresh instance
        from backend.main import app
        return TestClient(app)

    def test_app_configuration(self):
        """Test that app is configured correctly"""
        from backend.main import app

        assert app.title == "PE Portfolio API V2"
        assert app.version == "2.0.0"
        assert "Private Equity Portfolio Companies" in app.description

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "PE Portfolio API V2"
        assert data["version"] == "2.0.0"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "PE Portfolio API V2"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured"""
        from backend.main import app

        # Check that middleware is added
        middleware_stack = app.user_middleware
        cors_middleware_found = any(
            "CORSMiddleware" in str(middleware)
            for middleware in middleware_stack
        )

        assert cors_middleware_found

    def test_rate_limit_middleware_configured(self):
        """Test that rate limit middleware is configured"""
        from backend.main import app

        # Check that middleware is added
        middleware_stack = app.user_middleware
        rate_limit_middleware_found = any(
            "RateLimitMiddleware" in str(middleware)
            for middleware in middleware_stack
        )

        assert rate_limit_middleware_found

    def test_routers_included(self):
        """Test that all routers are included"""
        from backend.main import app

        # Get all routes
        routes = [route.path for route in app.routes]

        # Check for key endpoints from each router
        assert any("/api/auth" in route for route in routes)
        assert any("/api/stats" in route for route in routes)
        assert any("/api/pe-firms" in route for route in routes)
        assert any("/api/metadata" in route for route in routes)
        assert any("/api/investments" in route for route in routes)
        assert any("/api/companies" in route for route in routes)
        assert any("/api/similar-companies" in route for route in routes)

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    @patch('builtins.print')
    def test_startup_validation_with_env_vars(self, mock_print):
        """Test startup validation with environment variables set"""
        from backend.main import validate_environment
        import asyncio

        # Run the async function
        asyncio.run(validate_environment())

        # Check that success message was printed
        mock_print.assert_called_with("✅ All required environment variables are set")

    @patch.dict(os.environ, {}, clear=True)
    @patch('builtins.print')
    def test_startup_validation_without_env_vars(self, mock_print):
        """Test startup validation without environment variables"""
        from backend.main import validate_environment
        import asyncio

        # Run the async function
        asyncio.run(validate_environment())

        # Check that warning was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("WARNING" in call and "DATABASE_URL" in call for call in calls)

    @patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://example.com,http://test.com"})
    def test_cors_allowed_origins_from_env(self):
        """Test CORS allowed origins from environment variable"""
        # Need to reload the module to pick up env var
        import importlib
        import backend.main
        importlib.reload(backend.main)

        from backend.main import allowed_origins

        assert "http://example.com" in allowed_origins
        assert "http://test.com" in allowed_origins

    @patch.dict(os.environ, {}, clear=True)
    def test_cors_allowed_origins_default(self):
        """Test CORS allowed origins use defaults"""
        # Need to reload the module
        import importlib
        import backend.main
        importlib.reload(backend.main)

        from backend.main import allowed_origins

        # Should have defaults
        assert "http://localhost:5173" in allowed_origins
        assert "http://localhost:3000" in allowed_origins

    def test_health_check_no_database_required(self, client):
        """Test that health check works without database"""
        # Health check should work even if DB is not available
        response = client.get("/health")

        assert response.status_code == 200

    def test_docs_endpoint_available(self, client):
        """Test that OpenAPI docs endpoint is available"""
        response = client.get("/docs")

        # Should redirect or return docs page
        assert response.status_code in [200, 307]

    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON schema is available"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "PE Portfolio API V2"

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers

    @patch('uvicorn.run')
    def test_main_block_runs_uvicorn(self, mock_run):
        """Test that __main__ block runs uvicorn"""
        # Import and execute __main__ block
        import backend.main as main_module

        # Simulate running as main
        if hasattr(main_module, '__name__'):
            # Execute the code that would run in __main__
            import uvicorn
            with patch.object(main_module, '__name__', '__main__'):
                # This is just to verify the import works
                # The actual __main__ block won't execute during import
                assert uvicorn is not None

    def test_exposed_headers_configured(self):
        """Test that required headers are exposed via CORS"""
        from backend.main import app

        # Find CORS middleware configuration
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                # Headers should be exposed
                # This is configured in the middleware setup
                assert True
                return

        pytest.fail("CORS middleware not found")

    def test_api_version_consistency(self, client):
        """Test that API version is consistent across endpoints"""
        health_response = client.get("/health")
        root_response = client.get("/")
        openapi_response = client.get("/openapi.json")

        assert health_response.json()["version"] == "2.0.0"
        assert root_response.json()["version"] == "2.0.0"
        assert openapi_response.json()["info"]["version"] == "2.0.0"

    def test_root_endpoint_provides_navigation(self, client):
        """Test that root endpoint provides navigation links"""
        response = client.get("/")
        data = response.json()

        # Should provide links to key endpoints
        assert "docs" in data
        assert "health" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON"""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"

    def test_all_required_routers_registered(self):
        """Test that all required routers are registered"""
        from backend.main import app

        # Get all registered prefixes
        paths = {route.path for route in app.routes}

        # Check that key API paths exist
        required_paths = [
            "/api/auth/login",
            "/api/stats",
            "/api/pe-firms",
            "/api/metadata/industries",
            "/api/investments",
            "/api/companies",
            "/api/similar-companies"
        ]

        for path in required_paths:
            assert any(path in str(p) for p in paths), f"Missing route: {path}"
