# pylint: disable=redefined-outer-name

from unittest.mock import patch, MagicMock
import pytest
import requests
from main import app

@pytest.fixture
def flask_client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_version_endpoint(flask_client):
    """Test the version endpoint returns correct information."""
    response = flask_client.get('/version')
    assert response.status_code == 200
    data = response.get_json()
    assert data['version'] == "0.3.1"
    assert "/temperature" in data['api_endpoints']
    assert "/version" in data['api_endpoints']

@patch('requests.get')
def test_average_temperature_success(mock_get, flask_client):
    """Test successful temperature retrieval from multiple boxes."""
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

    mock_get.side_effect = [
        create_mock_response(25.5),
        create_mock_response(26.0),
        create_mock_response(24.5)
    ]
    response = flask_client.get('/temperature')
    assert response.status_code == 200
    data = response.get_json()
    expected_avg = (25.5 + 26.0 + 24.5) / 3
    assert data['temperature'] == pytest.approx(expected_avg)
    assert data['unit'] == '°C'
    assert data['boxes_used'] == 3

@patch('requests.get')
def test_average_temperature_partial_failure(mock_get, flask_client):
    """Test scenario where some box temperature retrievals fail."""
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

    mock_get.side_effect = [
        create_mock_response(25.5),
        requests.RequestException("Connection Error"),
        requests.RequestException("Connection Error")
    ]
    response = flask_client.get('/temperature')
    # Even if some boxes fail, at least one successful reading should result in a 200
    assert response.status_code == 200
    data = response.get_json()
    assert data['temperature'] == 25.5
    assert data['unit'] == '°C'
    assert data['boxes_used'] == 1

@patch('requests.get')
def test_average_temperature_no_data(mock_get, flask_client):
    """Test scenario where no temperature data is available."""
    mock_get.side_effect = requests.RequestException("Connection Error")
    response = flask_client.get('/temperature')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'No temperature data available'
