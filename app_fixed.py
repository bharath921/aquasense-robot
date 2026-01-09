from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import traceback

app = Flask(__name__)

# Store sensor readings
sensor_data_log = []

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def predict_crop(temp, humidity, moisture, soil_type, distance=None):
    """Enhanced crop prediction with water table analysis"""
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
            # Confidence based on number of recommendations and factors
            confidence_score = min(95, crop_counts.most_common(1)[0][1] * 12 + len(confidence_factors) * 8 + 40)
            confidence = f"{confidence_score}%"
        else:
            predicted_crop = "Mixed Farming"
            confidence = "70%"
            
        return predicted_crop, confidence
        
    except Exception as e:
        print(f"❌ Crop prediction error: {e}")
        return "Mixed Farming", "60%"

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

WEB_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🌱 AquaSense Smart Agriculture System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 20px; margin: 15px 0; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2); }
        .status-good { border-left: 5px solid #4CAF50; }
        .status-warning { border-left: 5px solid #FF9800; }
        .status-danger { border-left: 5px solid #f44336; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .sensor-reading { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .timestamp { font-size: 12px; opacity: 0.8; }
        .endpoint-info { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin: 10px 0; }
        .code { font-family: monospace; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; margin: 5px 0; }
        .log-entry { background: rgba(0,0,0,0.2); padding: 10px; margin: 5px 0; border-radius: 8px; font-size: 14px; }
        .refresh-btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px; }
        .refresh-btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 AquaSense Smart Agriculture System</h1>
            <p>Real-time Sensor Monitoring & Crop Prediction</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📡 Server Status</h2>
                <div class="status-good">
                    <p><strong>Status:</strong> ✅ Active and Running</p>
                    <p><strong>Total Readings:</strong> {{ total_readings }}</p>
                    <p><strong>Last Updated:</strong> {{ current_time }}</p>
                </div>
                
                <div class="endpoint-info">
                    <h3>🔗 ESP8266 Connection Info</h3>
                    <p><strong>Send data to:</strong></p>
                    <div class="code">http://192.168.181.232:5000/data</div>
                    <p><strong>Method:</strong> POST</p>
                    <p><strong>Content-Type:</strong> application/json</p>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 Latest Sensor Data</h2>
                {% if latest_reading %}
                <div class="sensor-reading">🌡️ Temperature: {{ "%.1f"|format(latest_reading.temperature) }}°C</div>
                <div class="sensor-reading">💧 Air Humidity: {{ "%.1f"|format(latest_reading.humidity) }}%</div>
                <div class="sensor-reading">🌱 Soil Moisture: {{ "%.1f"|format(latest_reading.moisture) }}%</div>
                <div class="sensor-reading" style="border-left: 4px solid #2196F3; padding-left: 15px; background: rgba(33,150,243,0.1);">
                    🌊 Water Table Depth: {{ "%.1f"|format(latest_reading.distance) }}cm
                    {% if latest_reading.distance < 15 %}
                        <span style="color: #4CAF50;"> ✅ Shallow - Good water access</span>
                    {% elif latest_reading.distance < 30 %}
                        <span style="color: #FF9800;"> ⚠️ Moderate - Some irrigation needed</span>
                    {% else %}
                        <span style="color: #f44336;"> 🚨 Deep - Frequent irrigation required</span>
                    {% endif %}
                </div>
                <div class="sensor-reading">🏔️ Soil Type: {{ latest_reading.soil_type }}</div>
                <div class="timestamp">{{ latest_reading.timestamp }}</div>
                {% else %}
                <p>⏳ Waiting for ESP8266 data...</p>
                <p>Make sure your ESP8266 is connected and sending data.</p>
                {% endif %}
            </div>
        </div>
        
        {% if latest_analysis %}
        <div class="card status-good">
            <h2>🤖 AI Analysis Results</h2>
            <div class="grid">
                <div>
                    <h3>🌾 Crop Recommendation</h3>
                    <p><strong>Recommended:</strong> {{ latest_analysis.predicted_crop }}</p>
                    <p><strong>Confidence:</strong> {{ latest_analysis.confidence }}</p>
                </div>
                <div>
                    <h3>💧 Water Management</h3>
                    <p><strong>Status:</strong> {{ latest_analysis.water_status }}</p>
                    <p><strong>Irrigation:</strong> {{ latest_analysis.irrigation_needed }}</p>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="card">
            <h2>🌾 Recommended Crop Details</h2>
            {% if sensor_data_log and sensor_data_log[-1].analysis %}
                {% set crop_name = sensor_data_log[-1].analysis.predicted_crop %}
                {% set crop_details = get_crop_details(crop_name) %}
                
                <div class="status-good">
                    <h3>{{ crop_details.name }}</h3>
                    <p><strong>Description:</strong> {{ crop_details.description }}</p>
                    
                    <div class="grid" style="margin: 15px 0;">
                        <div class="endpoint-info">
                            <h4>🌱 Optimal Growing Conditions</h4>
                            <p><strong>Temperature:</strong> {{ crop_details.optimal_conditions.temperature }}</p>
                            <p><strong>Humidity:</strong> {{ crop_details.optimal_conditions.humidity }}</p>
                            <p><strong>Soil Moisture:</strong> {{ crop_details.optimal_conditions.moisture }}</p>
                            <p><strong>Soil Type:</strong> {{ crop_details.optimal_conditions.soil }}</p>
                            <p><strong>pH Level:</strong> {{ crop_details.optimal_conditions.ph }}</p>
                            {% if crop_details.optimal_conditions.water_table %}
                            <p><strong>🌊 Water Table:</strong> {{ crop_details.optimal_conditions.water_table }}</p>
                            {% endif %}
                        </div>
                        
                        <div class="endpoint-info">
                            <h4>📊 Crop Information</h4>
                            <p><strong>Growing Period:</strong> {{ crop_details.growing_period }}</p>
                            <p><strong>Planting Season:</strong> {{ crop_details.planting_season }}</p>
                            <p><strong>Expected Yield:</strong> {{ crop_details.yield }}</p>
                            <p><strong>Market Value:</strong> {{ crop_details.market_value }}</p>
                        </div>
                    </div>
                    
                    <div class="endpoint-info">
                        <h4>💡 Care Tips & Best Practices</h4>
                        {% for tip in crop_details.care_tips %}
                            <p>• {{ tip }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="code">
                        <strong>🥗 Nutritional Information:</strong><br>
                        {{ crop_details.nutrition }}
                    </div>
                </div>
            {% else %}
                <p>🔄 Crop details will appear here once sensor data is received and analyzed.</p>
                <p>Connect your ESP8266 to see personalized crop recommendations!</p>
                
                <div class="endpoint-info">
                    <h4>🌾 Available Crop Database</h4>
                    <p>Our system can provide detailed information for:</p>
                    <div class="code">
                        Rice • Wheat • Bajra (Pearl Millet) • Maize • Cotton<br>
                        Sugarcane • Potato • Groundnut • And many more...
                    </div>
                </div>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>📋 Recent Activity Log</h2>
            <div style="max-height: 400px; overflow-y: auto;">
                {% for log in recent_logs %}
                <div class="log-entry">
                    <strong>{{ log.timestamp }}</strong> - 
                    🌡️{{ "%.1f"|format(log.temperature) }}°C, 
                    💧{{ "%.1f"|format(log.humidity) }}%, 
                    🌱{{ "%.1f"|format(log.moisture) }}%
                </div>
                {% endfor %}
                {% if not recent_logs %}
                <p>No data received yet. ESP8266 will appear here when connected.</p>
                {% endif %}
            </div>
        </div>
        
        <div class="card">
            <h2>⚙️ ESP8266 Setup Instructions</h2>
            <ol>
                <li><strong>Update WiFi credentials</strong> in the Arduino code:
                    <div class="code">
                        const char* ssid = "YOUR_WIFI_NAME";<br>
                        const char* password = "YOUR_WIFI_PASSWORD";
                    </div>
                </li>
                <li><strong>Install required libraries</strong> in Arduino IDE:
                    <div class="code">ESP8266WiFi, ArduinoJson, DHT</div>
                </li>
                <li><strong>Upload the code</strong> to your ESP8266</li>
                <li><strong>Open Serial Monitor</strong> (115200 baud) to see output</li>
                <li><strong>Data will appear</strong> on this page automatically!</li>
            </ol>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
        
        // Show connection status
        console.log("🌱 AquaSense Dashboard Loaded");
        console.log("📡 Waiting for ESP8266 data...");
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    """Home page with real-time dashboard"""
    latest_reading = sensor_data_log[-1] if sensor_data_log else None
    latest_analysis = getattr(latest_reading, 'analysis', None) if latest_reading else None
    
    return render_template_string(WEB_TEMPLATE, 
        total_readings=len(sensor_data_log),
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        latest_reading=latest_reading,
        latest_analysis=latest_analysis,
        recent_logs=sensor_data_log[-10:] if sensor_data_log else [],
        sensor_data_log=sensor_data_log,
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
def receive_data():
    """Receive sensor data from ESP8266"""
    try:
        print("\n" + "="*50)
        print("📡 NEW REQUEST TO /data")
        print("📩 Raw data:", request.data.decode('utf-8') if request.data else 'No data')
        print("📋 Headers:", dict(request.headers))
        
        # Parse JSON
        if not request.data:
            return jsonify({"error": "No data received"}), 400
            
        data = request.get_json(force=True)
        print("📥 Parsed JSON:", data)
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract values safely
        temp = safe_float(data.get("temp") or data.get("temperature"), 25.0)
        humidity = safe_float(data.get("humidity"), 50.0)
        moisture = safe_float(data.get("soil_moisture") or data.get("moisture"), 0.1)
        distance = safe_float(data.get("distance"), -1.0)
        soil_type = str(data.get("soil_type", "Loamy"))
        
        print(f"🔍 Extracted values:")
        print(f"   Temperature: {temp}°C")
        print(f"   Humidity: {humidity}%") 
        print(f"   Moisture: {moisture}%")
        print(f"   Distance: {distance}cm")
        print(f"   Soil Type: {soil_type}")
        
        # Handle edge cases
        if moisture <= 0:
            print("⚠️ Moisture is zero or negative, setting to 0.1%")
            moisture = 0.1
            
        # Make predictions with distance integration
        crop, confidence = predict_crop(temp, humidity, moisture, soil_type, distance)
        water_status, irrigation, water_table = analyze_water(moisture, soil_type, humidity, distance)
        
        # Store record with analysis
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temp,
            "humidity": humidity,
            "moisture": moisture,
            "distance": distance,
            "soil_type": soil_type,
            "raw_data": data,
            "analysis": {
                "predicted_crop": crop,
                "confidence": confidence,
                "water_status": water_status,
                "irrigation_needed": irrigation,
                "water_table_estimate": water_table
            }
        }
        
        sensor_data_log.append(record)
        if len(sensor_data_log) > 100:
            sensor_data_log.pop(0)
        
        print(f"💾 Stored record #{len(sensor_data_log)}")
        print(f"🤖 Predictions:")
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
                "confidence": confidence,
                "water_status": water_status,
                "irrigation_needed": irrigation,
                "water_table_estimate": water_table
            },
            "total_readings": len(sensor_data_log)
        }
        
        print("✅ Sending successful response")
        print("="*50 + "\n")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ ERROR in /data endpoint: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        
        error_response = {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_type": type(e).__name__
        }
        
        print(f"🔥 Sending error response: {error_response}")
        print("="*50 + "\n")
        return jsonify(error_response), 200  # Return 200 to help ESP8266

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get all sensor data logs"""
    return jsonify({
        "total_readings": len(sensor_data_log),
        "latest_readings": sensor_data_log[-10:] if sensor_data_log else [],
        "all_readings": sensor_data_log
    })

if __name__ == '__main__':
    print("🌱 Starting AquaSense Flask Server...")
    print("🔧 Server will run on:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000") 
    print("   • Your network IP on port 5000")
    print("📡 ESP8266 can send data to /data endpoint")
    print("🧪 Test with /test endpoint")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        traceback.print_exc()