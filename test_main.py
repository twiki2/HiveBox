# pylint: disable=redefined-outer-name
from unittest.mock import patch, MagicMock
import pytest
import requests
from main import app

@pytest.fixture
def client():
    """Provide a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_api_response():
    """Create a reusable mock response for temperature sensor data."""
    def _mock_response(temp_value=None):
        mock = MagicMock()
        if temp_value is not None:
            mock.json.return_value = {
                'sensors': [
                    {'title': 'Temperatur', 'lastMeasurement': {'value': str(temp_value)}}
                ]
            }
        return mock
    return _mock_response

def test_version_endpoint(client):
    """Verify the /version endpoint returns correct version and endpoints."""
    response = client.get('/version')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    assert data['version'] == "1.0.1", f"Expected version '1.0.1', got {data['version']}"
    assert data['api_endpoints'] == ["/", "/temperature", "/version", "/metrics"], \
        f"Unexpected endpoints: {data['api_endpoints']}"

@patch('requests.get')
def test_temperature_successful_retrieval(mock_get, client, mock_api_response):
    """Verify average temperature calculation with successful API responses."""
    mock_get.side_effect = [
        mock_api_response(25.5),
        mock_api_response(26.0),
        mock_api_response(24.5)
    ]
    response = client.get('/temperature')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    expected_avg = (25.5 + 26.0 + 24.5) / 3
    assert data['temperature'] == pytest.approx(expected_avg), \
        f"Expected temperature {expected_avg}, got {data['temperature']}"
    assert data['unit'] == "°C", f"Expected unit '°C', got {data['unit']}"
    assert data['boxes_used'] == 3, f"Expected 3 boxes, got {data['boxes_used']}"
    assert data['Status'] == "Good", f"Expected status 'Good', got {data['Status']}"

@patch('requests.get')
def test_temperature_partial_failure(mock_get, client, mock_api_response):
    """Verify handling of partial API failures with at least one successful response."""
    mock_get.side_effect = [
        mock_api_response(25.5),
        requests.RequestException("Connection Error"),
        requests.RequestException("Connection Error")
    ]
    response = client.get('/temperature')
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    assert data['temperature'] == 25.5, f"Expected temperature 25.5, got {data['temperature']}"
    assert data['unit'] == "°C", f"Expected unit '°C', got {data['unit']}"
    assert data['boxes_used'] == 1, f"Expected 1 box, got {data['boxes_used']}"
    assert data['Status'] == "Good", f"Expected status 'Good', got {data['Status']}"

@patch('requests.get')
def test_temperature_no_data(mock_get, client):
    """Verify error handling when no temperature data is available."""
    mock_get.side_effect = [requests.RequestException("Connection Error")] * 3
    response = client.get('/temperature')
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
    data = response.get_json()
    assert data == {"error": "No temperature data available"}, \
        f"Expected error message, got {data}"
