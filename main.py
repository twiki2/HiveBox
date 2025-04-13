import os
import logging
from flask import Flask, jsonify
import requests
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Constants
DEFAULT_APP_VERSION = "0.0.0"
APP_VERSION = os.getenv('APPVERSION', DEFAULT_APP_VERSION)
DEFAULT_BOX_IDS = "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
BOX_IDS = os.getenv('BOX_IDS', DEFAULT_BOX_IDS).split(',')
OPEN_SENSE_MAP_API_URL = "https://api.opensensemap.org/boxes"
REQUEST_TIMEOUT = 5

app = Flask(__name__)
metrics = PrometheusMetrics(app)

def get_temperature_status(temp):
    if temp < 10:
        return "Too Cold"
    elif temp > 37:
        return "Too Hot"
    elif 11 <= temp <= 36:
        return "Good"
    return "Can't Decide"

@app.route('/')
@app.route('/temperature')
def average_temperature():
    temperatures = []
    for box_id in BOX_IDS:
        try:
            response = requests.get(
                f"{OPEN_SENSE_MAP_API_URL}/{box_id}", 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            box_data = response.json()

            temp_sensor = next(
                (sensor for sensor in box_data['sensors'] if sensor['title'] == 'Temperatur'),
                None
            )

            if temp_sensor and 'lastMeasurement' in temp_sensor:
                temperature = float(temp_sensor['lastMeasurement']['value'])
                temperatures.append(temperature)

        except requests.RequestException as e:
            logger.error(f"Error fetching temperature for box {box_id}: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error processing data for box {box_id}: {e}")

    if not temperatures:
        return jsonify({"error": "No temperature data available"}), 404

    avg_temp = sum(temperatures) / len(temperatures)
    return jsonify({
        "temperature": round(avg_temp, 2),
        "unit": "°C",
        "boxes_used": len(temperatures),
        "Status": get_temperature_status(avg_temp)
    })

@app.route('/version')
def version():
    return jsonify({
        "version": APP_VERSION,
        "api_endpoints": ["/", "/temperature", "/version", "/metrics"]
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
