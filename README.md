# 🌱 AquaSense Smart Agriculture Robot System

AquaSense is a cyber-physical system designed to optimize crop yield and water management. It integrates an **ESP8266-based robot hardware platform** with a **Python/Flask machine learning backend** to deliver real-time soil analysis, water table monitoring, and crop recommendations.

---

## 📐 System Architecture

The project consists of two primary subsystems:

1. **Hardware (ESP8266)**:
   * Periodically monitors soil moisture, air temperature, humidity, and water table depth (using an ultrasonic distance sensor).
   * Transmits raw sensor payloads to the Flask API endpoint via HTTP POST.
2. **Backend & Dashboard (Flask + Machine Learning)**:
   * **API Endpoint (`/data`)**: Receives and logs real-time sensor metrics.
   * **Machine Learning Model**: Analyzes sensor features to recommend optimal crops.
   * **Rule-Based Heuristics**: Acts as a robust fallback to ensure safety and precision.
   * **Web Dashboard**: Displays live metrics, historical logs, crop profile cards, and a sandbox simulator.

---

## 🤖 Machine Learning Model

The crop prediction model is trained on a clean subset of environmental conditions to classify and recommend crops based on physical parameters:
* **Features Used**: Temperature, Humidity, Moisture, and Soil Type (encoded).
* **Best Classifier**: Tuned Random Forest Classifier.

### Model Accuracy Metrics
* **Base Features (11 Crop Classes)**: **~69.63%** Mean 5-Fold Cross-Validation Accuracy.
* **Top 5 Regional Crops** (Sugarcane, Cotton, Millets, Paddy, Pulses): **~91.21%** Cross-Validation Accuracy.

> [!NOTE]
> Training on rows beyond the first 99 in `data_core.csv` drops performance dramatically (to ~9% accuracy) due to corrupted/random noise in the larger raw database.

---

## 🚀 Setup & Execution

### 1. Python Environment Setup
Install dependencies:
```bash
pip install flask pandas numpy scikit-learn xgboost jinja2
```

### 2. Train the Machine Learning Model
Train and save the optimized crop prediction model:
```bash
python train_models.py
```
This generates the serialized model and encoder files:
* `crop_predictor.pkl`
* `soil_encoder.pkl`
* `crop_encoder.pkl`

### 3. Run the Flask Web Application
Start the server:
```bash
python app_fixed.py
```
Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

### 4. Run Pipeline Integration Tests
To verify the ML prediction pipeline and server communication:
```bash
python test_ml_pipeline.py
```

---

## 📡 ESP8266 Node Setup

1. Open `ESP8266_AquaSense_Complete.ino` in the Arduino IDE.
2. Install the following libraries:
   * `ESP8266WiFi`
   * `ArduinoJson`
   * `DHT`
3. Configure your WiFi credentials and the target Flask server IP:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* serverUrl = "http://<YOUR_LAPTOP_IP>:5000/data";
   ```
4. Flash the code to your ESP8266 board.
