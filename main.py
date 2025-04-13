import os
from flask import Flask, jsonify
import requests
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics

load_dotenv()

# Configuring env
DEFAULT_APP_VERSION = "0.0.0"
APP_VERSION = os.getenv('APPVERSION', DEFAULT_APP_VERSION)
DEFAULT_BOX_IDS = "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
BOX_IDS = os.getenv('BOX_IDS', DEFAULT_BOX_IDS).split(',')
OPEN_SENSE_MAP_API_URL = "https://api.opensensemap.org/boxes"

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route('/')
@app.route('/temperature')
def average_temperature():
    temperatures = []
    for box_id in BOX_IDS:
        try:
            response = requests.get(f"{OPEN_SENSE_MAP_API_URL}/{box_id}", timeout=5)
            box_data = response.json()

            temp_sensor = next(
                (sensor for sensor in box_data['sensors'] if sensor['title'] == 'Temperatur'),
                None
            )

            if temp_sensor and 'lastMeasurement' in temp_sensor:
                temperature = float(temp_sensor['lastMeasurement']['value'])
                temperatures.append(temperature)

        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error fetching temperature for box {box_id}: {e}")

    if temperatures:
        avg_temp = sum(temperatures) / len(temperatures)
        if avg_temp < 10:
            status = "Too Cold"
        elif avg_temp > 37:
            status = "Too Hot"
        elif  11 <= avg_temp <= 36:
            status = "Good"
        else :
            status = "Can't Decide"
        return jsonify({
            "temperature": avg_temp,
            "unit": "°C",
            "boxes_used": len(temperatures),
            "Status": status
        })
    return jsonify({"error": "No temperature data available"}), 404

@app.route('/version')
def version():
    return jsonify({
        "version": APP_VERSION,
        "api_endpoints": ["/", "/temperature", "/version","/metrics"]
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=False)
