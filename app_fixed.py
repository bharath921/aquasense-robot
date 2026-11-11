from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
import json
from math import isfinite
import sqlite3
import traceback
import pickle
import os
import pandas as pd

app = Flask(__name__)

app.config["DATABASE"] = Path(__file__).resolve().with_name("aquasense.sqlite3")


def open_database():
    db = sqlite3.connect(app.config["DATABASE"])
    with db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY,
                recorded_at TEXT NOT NULL,
                soil_moisture REAL NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS readings_time ON readings (recorded_at)")
    return db


def reading_count(db):
    return db.execute("SELECT COUNT(*) FROM readings").fetchone()[0]


def recent_readings(db, limit):
    rows = db.execute(
        "SELECT payload FROM readings ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [json.loads(payload) for (payload,) in reversed(rows)]

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

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None:
            return default
        number = float(value)
        return number if isfinite(number) else default
    except (TypeError, ValueError):
        return default

def predict_crop(temp, humidity, moisture, soil_type, distance=None):
    crop, confidence, _ = predict_crop_with_method(temp, humidity, moisture, soil_type, distance)
    return crop, confidence


def predict_crop_with_method(temp, humidity, moisture, soil_type, distance=None):
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
            class_index = list(ml_model.classes_).index(pred_encoded)
            confidence_score = float(probabilities[class_index]) * 100
            confidence = f"{confidence_score:.1f}%"
            
            print(f"[ML] Prediction: {predicted_crop} ({confidence})")
            return predicted_crop, confidence, type(ml_model).__name__
            
        except Exception as ml_err:
            print(f"[WARN] ML prediction failed, falling back to heuristics: {ml_err}")

    # 2. Heuristic Rule-Based Fallback
    try:
        crop_recommendations = []
        confidence_factors = []
        
        # Temperature-based recommendations
        if 15 <= temp <= 25:
            crop_recommendations.extend(["Wheat", "Potato", "Barley"])
            confidence_factors.append("optimal_temp")
        elif 20 <= temp <= 30:
            if humidity > 60:
                crop_recommendations.extend(["Rice", "Sugarcane"])
            else:
                crop_recommendations.extend(["Maize", "Cotton"])
            confidence_factors.append("good_temp")
        elif temp > 30:
            crop_recommendations.extend(["Bajra", "Sorghum", "Groundnut"])
            confidence_factors.append("hot_climate")
        
        if moisture < 30:
            crop_recommendations.extend(["Bajra", "Groundnut", "Sorghum"])
            confidence_factors.append("drought_tolerant")
        elif 30 <= moisture <= 70:
            crop_recommendations.extend(["Wheat", "Maize", "Cotton"])
            confidence_factors.append("moderate_water")
        else:
            crop_recommendations.extend(["Rice", "Sugarcane"])
            confidence_factors.append("high_water")
        
        # Distance-based water table analysis
        if distance is not None:
            if distance < 15:  # Shallow water table
                crop_recommendations.extend(["Rice", "Sugarcane", "Jute"])
                confidence_factors.append("shallow_water_table")
            elif distance < 30:  # Moderate water access
                crop_recommendations.extend(["Wheat", "Maize", "Cotton"])
                confidence_factors.append("moderate_water_access")
            else:  # Deep water table - drought resistant crops
                crop_recommendations.extend(["Bajra", "Groundnut", "Millets"])
                confidence_factors.append("deep_water_table")
        
        # Soil type adjustments
        if soil_type.lower() in ['clay', 'loamy']:
            crop_recommendations.extend(["Rice", "Wheat", "Cotton"])
        elif soil_type.lower() == 'sandy':
            crop_recommendations.extend(["Groundnut", "Bajra", "Watermelon"])
        
        # Calculate most suitable crop
        from collections import Counter
        crop_counts = Counter(crop_recommendations)
        
        if crop_counts:
            predicted_crop = crop_counts.most_common(1)[0][0]
            confidence_score = min(95, crop_counts.most_common(1)[0][1] * 12 + len(confidence_factors) * 8 + 40)
            confidence = f"{confidence_score}% (Rule-based)"
        else:
            predicted_crop = "Mixed Farming"
            confidence = "70% (Rule-based)"
            
        print(f"[INFO] Heuristic Fallback Prediction: {predicted_crop} ({confidence})")
        return predicted_crop, confidence, "Rule-based"
        
    except Exception as e:
        print(f"❌ Crop prediction error: {e}")
        return "Mixed Farming", "60%", "Rule-based"

def analyze_water(moisture, soil_type, humidity, distance=None):
    """Enhanced water analysis with distance-based water table detection"""
    try:
        # Base water analysis from moisture
        if moisture < 20:
            water_status = "Low"
            irrigation = "Immediate irrigation required"
        elif moisture < 40:
            water_status = "Below Optimal"
            irrigation = "Light irrigation recommended"
        elif moisture < 70:
            water_status = "Optimal"
            irrigation = "No irrigation needed"
        else:
            water_status = "High"
            irrigation = "Avoid watering - risk of waterlogging"
        
        # Enhanced analysis with distance (water table depth)
        if distance is not None:
            if distance < 10:  # Very close to water source/high water table
                water_table = f"Shallow ({distance:.1f}cm) - High water table"
                if moisture > 60:
                    irrigation = "No irrigation - natural water available"
                    water_status = "Naturally High"
            elif distance < 25:  # Moderate distance
                water_table = f"Moderate depth ({distance:.1f}cm) - Good water access"
                if moisture < 30:
                    irrigation = "Light irrigation sufficient - water table accessible"
            elif distance < 50:  # Deeper water table
                water_table = f"Deep ({distance:.1f}cm) - Limited natural water"
                if moisture < 40:
                    irrigation = "Regular irrigation needed - deep water table"
            else:  # Very deep or no water detected
                water_table = f"Very deep ({distance:.1f}cm) - Rely on irrigation"
                irrigation = "Frequent irrigation required - no natural water source"
        else:
            water_table = "Unknown depth - sensor not available"
        
        return water_status, irrigation, water_table
        
    except Exception as e:
        print(f"❌ Water analysis error: {e}")
        return "Unknown", "Check manually", "Sensor error"

def get_crop_details(crop_name):
    """Comprehensive crop database with growing details"""
    crop_database = {
        "Rice": {
            "name": "Rice (Oryza sativa)",
            "description": "Staple cereal grain crop, ideal for shallow water table areas",
            "optimal_conditions": {
                "temperature": "20-35°C",
                "humidity": "70-80%",
                "moisture": "80-90%",
                "soil": "Clay, Loamy",
                "ph": "5.5-6.5",
                "water_table": "Shallow (<20cm) - Benefits from high water table"
            },
            "growing_period": "120-150 days",
            "planting_season": "Kharif (June-July) or Rabi (Nov-Dec)",
            "yield": "4-6 tons per hectare",
            "care_tips": [
                "🌾 Maintain standing water 2-5cm deep",
                "💧 Apply nitrogen fertilizer in splits",
                "🌱 Control weeds in first 45 days",
                "⚠️ Watch for blast and brown spot diseases"
            ],
            "market_value": "₹20-25 per kg",
            "nutrition": "Carbohydrates: 78g, Protein: 7g, Fiber: 1.3g per 100g"
        },
        "Wheat": {
            "name": "Wheat (Triticum aestivum)",
            "description": "Major cereal grain, primary ingredient for bread and flour",
            "optimal_conditions": {
                "temperature": "15-25°C",
                "humidity": "50-70%",
                "moisture": "40-60%",
                "soil": "Loamy, Well-drained",
                "ph": "6.0-7.5"
            },
            "growing_period": "120-150 days",
            "planting_season": "Rabi (Nov-Dec)",
            "yield": "3-4 tons per hectare",
            "care_tips": [
                "🌾 Sow after monsoon when soil moisture is adequate",
                "💧 Apply phosphorus at sowing time",
                "🚿 Three irrigations: crown root, tillering, flowering",
                "🌕 Harvest when grains are hard and golden"
            ],
            "market_value": "₹22-28 per kg",
            "nutrition": "Carbohydrates: 71g, Protein: 13g, Fiber: 12.2g per 100g"
        },
        "Bajra": {
            "name": "Pearl Millet/Bajra (Pennisetum glaucum)",
            "description": "Drought-resistant cereal, perfect for deep water table areas",
            "optimal_conditions": {
                "temperature": "25-35°C",
                "humidity": "40-70%",
                "moisture": "25-50%",
                "soil": "Sandy, Well-drained",
                "ph": "6.5-7.5",
                "water_table": "Deep (>30cm) - Excellent for low water areas"
            },
            "growing_period": "70-110 days",
            "planting_season": "Kharif (June-July)",
            "yield": "1-3 tons per hectare",
            "care_tips": [
                "🌵 Highly drought tolerant - perfect for deep water table",
                "🌱 Minimal fertilizer requirements",
                "🏜️ Excellent for marginal and sandy lands",
                "💧 Requires minimal irrigation even with deep water sources",
                "🦅 Birds protection needed during maturity"
            ],
            "market_value": "₹25-35 per kg",
            "nutrition": "Protein: 11g, Iron: 3mg, Calcium: 42mg per 100g"
        }
    }
    
    return crop_database.get(crop_name, {
        "name": crop_name,
        "description": "Recommended crop based on current conditions",
        "optimal_conditions": {"note": "Specific details not available"},
        "care_tips": ["🌱 Monitor soil conditions", "💧 Provide adequate water", "🌾 Use appropriate fertilizers"]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with real-time dashboard"""
    with closing(open_database()) as db:
        sensor_data_log = recent_readings(db, 10)
        total_readings = reading_count(db)
        moisture_history = db.execute("""
            SELECT recorded_at, soil_moisture FROM readings
            WHERE recorded_at >= datetime('now', '-1 day')
            ORDER BY recorded_at, id
        """).fetchall()
    latest_reading = sensor_data_log[-1] if sensor_data_log else None
    latest_analysis = latest_reading["analysis"] if latest_reading else None
    
    return render_template(
        "dashboard.html",
        total_readings=total_readings,
        moisture_history=moisture_history,
        latest_reading=latest_reading,
        latest_analysis=latest_analysis,
        recent_logs=sensor_data_log,
        get_crop_details=get_crop_details
    )

@app.route('/test', methods=['GET', 'POST'])
def test():
    """Simple test endpoint"""
    if request.method == 'GET':
        return jsonify({
            "message": "Test GET successful! ✅",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        try:
            data = request.get_json(force=True) if request.data else {}
            return jsonify({
                "message": "Test POST successful! ✅",
                "received": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            return jsonify({
                "message": "Test POST failed ❌",
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

@app.route('/data', methods=['POST'])
@app.route('/simulate', methods=['POST'], endpoint='simulate')
def receive_data():
    """Receive sensor data from ESP8266"""
    try:
        print("\n" + "="*50)
        print("[INFO] NEW REQUEST TO /data")
        print("[INFO] Raw data:", request.data.decode('utf-8') if request.data else 'No data')
        print("[INFO] Headers:", dict(request.headers))
        
        # Parse JSON
        if not request.data:
            return jsonify({"error": "No data received"}), 400
            
        data = request.get_json(force=True)
        print("[INFO] Parsed JSON:", data)
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract values safely
        temp = safe_float(data.get("temp", data.get("temperature")), 25.0)
        humidity = safe_float(data.get("humidity"), 50.0)
        moisture = safe_float(data.get("soil_moisture", data.get("moisture")), 0.1)
        distance = safe_float(data.get("distance"), -1.0)
        soil_type = str(data.get("soil_type", "Loamy"))
        
        print(f"[INFO] Extracted values:")
        print(f"   Temperature: {temp}°C")
        print(f"   Humidity: {humidity}%") 
        print(f"   Moisture: {moisture}%")
        print(f"   Distance: {distance}cm")
        print(f"   Soil Type: {soil_type}")
        
        # Handle edge cases
        if moisture < 0:
            print("[WARN] Moisture is negative, setting to 0.1%")
            moisture = 0.1
            
        # Make predictions with distance integration
        crop, confidence, prediction_method = predict_crop_with_method(
            temp, humidity, moisture, soil_type, distance
        )
        water_status, irrigation, water_table = analyze_water(moisture, soil_type, humidity, distance)
        
        # Store record with analysis
        record = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temp,
            "humidity": humidity,
            "moisture": moisture,
            "distance": distance,
            "soil_type": soil_type,
            "raw_data": data,
            "analysis": {
                "predicted_crop": crop,
                "prediction_method": prediction_method,
                "confidence": confidence,
                "water_status": water_status,
                "irrigation_needed": irrigation,
                "water_table_estimate": water_table
            }
        }
        
        with closing(open_database()) as db, db:
            if request.path == "/data":
                db.execute("""
                    INSERT INTO readings (recorded_at, soil_moisture, payload)
                    VALUES (?, ?, ?)
                """, (record["timestamp"], moisture, json.dumps(record)))
            total_readings = reading_count(db)
        print(f"[INFO] Predictions:")
        print(f"   Crop: {crop} (Confidence: {confidence})")
        print(f"   Water: {water_status}")
        print(f"   Irrigation: {irrigation}")
        
        # Create response
        response = {
            "status": "success",
            "message": "Data received and analyzed successfully! ✅",
            "timestamp": record["timestamp"],
            "received_data": {
                "temperature": temp,
                "humidity": humidity, 
                "moisture": moisture,
                "soil_type": soil_type
            },
            "analysis": {
                "predicted_crop": crop,
                "prediction_method": prediction_method,
                "confidence": confidence,
                "water_status": water_status,
                "irrigation_needed": irrigation,
                "water_table_estimate": water_table
            },
            "total_readings": total_readings
        }
        
        print("[INFO] Sending successful response")
        print("="*50 + "\n")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[ERROR] ERROR in /data endpoint: {e}")
        print("[INFO] Full traceback:")
        traceback.print_exc()
        
        error_response = {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_type": type(e).__name__
        }
        
        print(f"[ERROR] Sending error response: {error_response}")
        print("="*50 + "\n")
        return jsonify(error_response), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get the latest 100 readings and the lifetime count."""
    with closing(open_database()) as db:
        sensor_data_log = recent_readings(db, 100)
        total_readings = reading_count(db)
    return jsonify({
        "total_readings": total_readings,
        "latest_readings": sensor_data_log[-10:] if sensor_data_log else [],
        "all_readings": sensor_data_log
    })

if __name__ == '__main__':
    print("[INFO] Starting AquaSense Flask Server...")
    print("[INFO] Server will run on:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000") 
    print("   • Your network IP on port 5000")
    print("[INFO] ESP8266 can send data to /data endpoint")
    print("[INFO] Test with /test endpoint")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        traceback.print_exc()
