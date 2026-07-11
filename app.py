from flask import Flask, request, jsonify
from datetime import datetime
import os
import pickle
import pandas as pd

app = Flask(__name__)

sensor_data_log = []

# Load ML model and encoders on startup
MODEL_PATH = 'crop_predictor.pkl'
SOIL_ENCODER_PATH = 'soil_encoder.pkl'
CROP_ENCODER_PATH = 'crop_encoder.pkl'

ml_model = None
soil_encoder = None
crop_encoder = None

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(SOIL_ENCODER_PATH) and os.path.exists(CROP_ENCODER_PATH):
        with open(MODEL_PATH, 'rb') as f:
            ml_model = pickle.load(f)
        with open(SOIL_ENCODER_PATH, 'rb') as f:
            soil_encoder = pickle.load(f)
        with open(CROP_ENCODER_PATH, 'rb') as f:
            crop_encoder = pickle.load(f)
        print("[ML] Model and Encoders loaded successfully!")
    else:
        print("[WARN] ML Model files not found. Using fallback rule-based predictions.")
except Exception as e:
    print(f"[ERROR] Error loading ML model: {e}")

# ---------- Helper functions ----------

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def predict_crop(temp, humidity, moisture, soil_type):
    """Enhanced crop prediction using ML model with a rule-based fallback"""
    # 1. Try ML Prediction
    if ml_model is not None and soil_encoder is not None and crop_encoder is not None:
        try:
            # Clean and encode soil type
            soil_type_clean = str(soil_type).strip().capitalize()
            if soil_type_clean not in soil_encoder.classes_:
                matched = False
                for c in soil_encoder.classes_:
                    if c.lower() == soil_type_clean.lower():
                        soil_type_clean = c
                        matched = True
                        break
                if not matched:
                    soil_type_clean = 'Sandy'
            
            soil_encoded = soil_encoder.transform([soil_type_clean])[0]
            
            # Predict using a DataFrame with correct feature names to avoid UserWarning
            features_df = pd.DataFrame(
                [[temp, humidity, moisture, soil_encoded]],
                columns=['Temparature', 'Humidity', 'Moisture', 'Soil Type Encoded']
            )
            pred_encoded = ml_model.predict(features_df)[0]
            predicted_crop = crop_encoder.inverse_transform([pred_encoded])[0]
            
            # Get confidence
            probabilities = ml_model.predict_proba(features_df)[0]
            confidence_score = float(probabilities[pred_encoded]) * 100
            confidence = f"{confidence_score:.1f}%"
            
            print(f"[ML] Prediction: {predicted_crop} ({confidence})")
            return predicted_crop, confidence
            
        except Exception as ml_err:
            print(f"[WARN] ML prediction failed, falling back to heuristics: {ml_err}")

    # 2. Heuristic Rule-Based Fallback
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
