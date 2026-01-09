from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

sensor_data_log = []

# ---------- Helper functions ----------

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def predict_crop(temp, humidity, moisture, soil_type):
    if moisture < 30:
        crop = "Bajra"
        confidence = "High"
    elif 30 <= moisture <= 60:
        crop = "Rice"
        confidence = "Medium"
    else:
        crop = "Wheat"
        confidence = "Low"
    return crop, confidence


def analyze_water_availability(moisture, soil_type, humidity):
    if moisture < 20:
        water_status = "Low"
        irrigation = "Required"
    elif 20 <= moisture <= 60:
        water_status = "Optimal"
        irrigation = "Not Required"
    else:
        water_status = "High"
        irrigation = "Avoid Watering"

    if soil_type.lower() == "clay":
        water_table = "High"
    elif soil_type.lower() == "sandy":
        water_table = "Low"
    else:
        water_table = "Moderate"

    return water_status, irrigation, water_table


def get_fertilizer_recommendation(soil_type, moisture):
    if soil_type.lower() == "sandy":
        return "Use compost or organic manure to retain moisture."
    elif soil_type.lower() == "clay":
        return "Use gypsum and mix organic matter for better aeration."
    else:
        return "Balanced NPK fertilizer recommended."


# ---------- Main route for receiving ESP8266 data ----------

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        print("� ENDPOINT /data HIT - Starting processing...")
        print("�📩 Raw request data:", request.data)
        print("📝 Request headers:", dict(request.headers))
        print("🌐 Request method:", request.method)

        # Parse JSON safely
        data = request.get_json(force=True)
        print("📥 Parsed JSON:", data)

        temp = safe_float(data.get("temp") or data.get("temperature"))
        humidity = safe_float(data.get("humidity"))
        moisture = safe_float(data.get("soil_moisture") or data.get("moisture"))
        distance = safe_float(data.get("distance"), -1)
        soil_type = str(data.get("soil_type", "Loamy"))

        print(f"🔍 Extracted → Temp={temp}, Humidity={humidity}, Moisture={moisture}, Distance={distance}, Soil={soil_type}")

        # Fix invalid readings
        if moisture <= 0:
            print("⚠️ Moisture invalid or zero — setting to 0.1%")
            moisture = 0.1
        if distance < 0:
            print("⚠️ Distance invalid — ignoring")

        # Log in memory
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temp,
            "humidity": humidity,
            "moisture": moisture,
            "distance": distance,
            "soil_type": soil_type
        }

        sensor_data_log.append(record)
        if len(sensor_data_log) > 100:
            sensor_data_log.pop(0)

        # Analyze
        crop, confidence = predict_crop(temp, humidity, moisture, soil_type)
        water_status, irrigation, water_table = analyze_water_availability(moisture, soil_type, humidity)
        fertilizer = get_fertilizer_recommendation(soil_type, moisture)

        response = {
            "status": "success",
            "message": "Data received successfully!",
            "analysis": {
                "predicted_crop": crop,
                "confidence": confidence,
                "water_status": water_status,
                "irrigation": irrigation,
                "water_table": water_table,
                "fertilizer_recommendation": fertilizer
            }
        }

        print("✅ Final response to ESP:", response)
        return jsonify(response), 200

    except Exception as e:
        print("❌ FULL ERROR TRACE:", e)
        import traceback
        traceback.print_exc()
        
        # Return error as 200 to help ESP8266 debugging
        error_response = {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print("🔥 Sending error response:", error_response)
        return jsonify(error_response), 200


# ---------- Home route ----------

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "AquaSense Flask Server Active 🌊",
        "received_records": len(sensor_data_log)
    })

@app.route('/test', methods=['GET', 'POST'])
def test_route():
    if request.method == 'GET':
        return jsonify({
            "message": "Test route working!",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "GET"
        })
    else:
        return jsonify({
            "message": "Test POST working!",
            "received_data": request.get_json(force=True) if request.data else {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "POST"
        })


# ---------- Start server ----------

if __name__ == '__main__':
    print("🌱 Starting AquaSense Flask Server...")
    print("🔧 Debug mode enabled for troubleshooting")
    app.run(host='0.0.0.0', port=5000, debug=True)
