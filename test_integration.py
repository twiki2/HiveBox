# pylint: disable=redefined-outer-name
import pytest
from main import app

@pytest.fixture
def client():
    """Provide a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_root_endpoint(client):
    """Test the root endpoint for a valid response."""
    response = client.get('/')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    assert "temperature" in data, "Expected 'temperature' in response"
    assert "unit" in data, "Expected 'unit' in response"
    assert "boxes_used" in data, "Expected 'boxes_used' in response"
    assert "Status" in data, "Expected 'Status' in response"

def test_version_endpoint(client):
    """Test the /version endpoint for correct version and endpoints."""
    response = client.get('/version')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    assert "version" in data, "Expected 'version' in response"
    assert "api_endpoints" in data, "Expected 'api_endpoints' in response"

def test_metrics_endpoint(client):
    """Test the /metrics endpoint for Prometheus metrics."""
    response = client.get('/metrics')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "flask_http_request_duration_seconds" in response.data.decode(), \
        "Expected Prometheus metrics in response"
