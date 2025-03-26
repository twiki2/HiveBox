from flask import Flask, jsonify
import requests

app = Flask(__name__)

APP_VERSION = "0.0.2"

BOX_IDS = [
    "5eba5fbad46fb8001b799786",
    "5c21ff8f919bf8001adf2488",
    "5ade1acf223bd80019a1011c"
]
OPEN_SENSE_MAP_API_URL = "https://api.opensensemap.org/boxes"

@app.route('/')
@app.route('/temperature')
def average_temperature():
    temperatures = []
    for box_id in BOX_IDS:
        try:
            response = requests.get(f"{OPEN_SENSE_MAP_API_URL}/{box_id}", timeout=5)
            box_data = response.json()
            
            temp_sensor = next(
                (sensor for sensor in box_data['sensors'] 
                 if sensor['title'] == 'Temperatur'), 
                None
            )
            
            if temp_sensor and 'lastMeasurement' in temp_sensor:
                temperature = float(temp_sensor['lastMeasurement']['value'])
                temperatures.append(temperature)
        
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error fetching temperature for box {box_id}: {e}")
    
    if temperatures:
        avg_temp = sum(temperatures) / len(temperatures)
        return jsonify({
            "temperature": avg_temp,
            "unit": "°C",
            "boxes_used": len(temperatures)
        })
    else:
        return jsonify({"error": "No temperature data available"}), 404

@app.route('/version')
def version():
    return jsonify({
        "version": APP_VERSION,
        "api_endpoints": ["/", "/temperature", "/version"]
    })

if __name__ == "__main__":
    app.run(debug=False)