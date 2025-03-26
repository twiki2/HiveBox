import pytest
import requests
from unittest.mock import patch, MagicMock
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_version_endpoint(client):
    """Test the version endpoint returns correct information."""
    response = client.get('/version')
    assert response.status_code == 200
    data = response.get_json()
    assert data['version'] == "0.0.2"
    assert "/temperature" in data['api_endpoints']
    assert "/version" in data['api_endpoints']

@patch('requests.get')
def test_average_temperature_success(mock_get, client):
    """Test successful temperature retrieval from multiple boxes."""
    # Create mock response objects that mimic requests.Response
    def create_mock_response(temp_value):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'sensors': [
                {
                    'title': 'Temperatur', 
                    'lastMeasurement': {'value': str(temp_value)}
                }
            ]
        }
        return mock_response

    # Mock responses for multiple box temperature readings
    mock_get.side_effect = [
        create_mock_response(25.5),
        create_mock_response(26.0),
        create_mock_response(24.5)
    ]
    
    response = client.get('/temperature')
    assert response.status_code == 200
    data = response.get_json()
    
    # Check average calculation
    expected_avg = (25.5 + 26.0 + 24.5) / 3
    assert data['temperature'] == pytest.approx(expected_avg)
    assert data['unit'] == '°C'
    assert data['boxes_used'] == 3

@patch('requests.get')
def test_average_temperature_partial_failure(mock_get, client):
    """Test scenario where some box temperature retrievals fail."""
    # Create mock response objects
    def create_mock_response(temp_value=None):
        mock_response = MagicMock()
        if temp_value is not None:
            mock_response.json.return_value = {
                'sensors': [
                    {
                        'title': 'Temperatur', 
                        'lastMeasurement': {'value': str(temp_value)}
                    }
                ]
            }
        else:
            mock_get.side_effect = requests.RequestException("Connection Error")
        return mock_response

    # Mock responses with one successful and two failed requests
    mock_get.side_effect = [
        create_mock_response(25.5),
        requests.RequestException("Connection Error"),
        requests.RequestException("Connection Error")
    ]
    
    response = client.get('/temperature')
    assert response.status_code == 200
    data = response.get_json()
    
    # Check average calculation with only one successful box
    assert data['temperature'] == 25.5
    assert data['unit'] == '°C'
    assert data['boxes_used'] == 1

@patch('requests.get')
def test_average_temperature_no_data(mock_get, client):
    """Test scenario where no temperature data is available."""
    # Simulate all requests failing
    mock_get.side_effect = requests.RequestException("Connection Error")
    
    response = client.get('/temperature')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'No temperature data available'