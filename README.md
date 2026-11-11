# 🌱 AquaSense Smart Agriculture Robot System

AquaSense is a cyber-physical system designed to optimize crop yield and water management. It integrates an **ESP8266-based robot hardware platform** with a **Python/Flask machine learning backend** to deliver real-time soil analysis, water table monitoring, and crop recommendations.

---

## 📐 System Architecture

The project consists of two primary subsystems:

1. **Hardware (ESP8266)**:
   * Periodically monitors soil moisture, air temperature, humidity, and water table depth (using an ultrasonic distance sensor).
   * Transmits raw sensor payloads to the Flask API endpoint via HTTP POST.
2. **Backend & Dashboard (Flask + Machine Learning)**:
  * **API Endpoint (`/data`)**: Receives sensor readings and saves them with UTC timestamps in `aquasense.sqlite3` beside `app_fixed.py`.
   * **Machine Learning Model**: Analyzes sensor features to recommend optimal crops.
   * **Rule-Based Heuristics**: Acts as a robust fallback to ensure safety and precision.
  * **Web Dashboard**: Shows recent readings and a 24-hour soil moisture chart. The sandbox uses `/simulate` so it can display predictions without writing to the history. `/logs` returns the latest 100 saved records and a lifetime count.

---

## 🤖 Machine Learning Model

The crop prediction model is trained on a clean subset of environmental conditions to classify and recommend crops based on physical parameters:
* **Features Used**: Temperature, Humidity, Moisture, and Soil Type (encoded).
* **Model Selection**: Five classifiers compared by mean macro F1 on stratified cross-validation within the training split.

### Model Accuracy Metrics

The evaluation uses the project's existing 99-row subset, with 74 rows for training and 25 held out for testing across 11 crops. XGBoost scored highest in training cross-validation (macro F1 **56.67%**).

| Classifier | Mean training CV macro F1 |
| --- | ---: |
| XGBoost | 56.67% |
| Random Forest | 53.09% |
| Support Vector Machine | 44.06% |
| Multi-Layer Perceptron | 32.30% |
| K-Nearest Neighbors | 28.06% |

| Holdout metric | Score |
| --- | ---: |
| Accuracy | 64.00% |
| Majority-class baseline accuracy | 12.00% |
| Balanced accuracy | 62.12% |
| Macro precision | 64.55% |
| Macro recall | 62.12% |
| Macro F1 | 60.45% |
| Weighted F1 | 63.13% |

Macro scores give each crop equal weight. Weighted scores give crops with more test examples more weight. The small test set provides an experimental estimate. Repeat the evaluation and view per-crop metrics and the confusion matrix with `python train_models.py --evaluate-only`. The bundled XGBoost model was refit on all 99 rows after evaluation. The dashboard displays the prediction method alongside the crop suggestion.

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

SQLite is included with Python. The app creates its database on first use and reads it again after a restart.

### 4. Run the Prediction Smoke Test
To check that the prediction function returns a result:
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
