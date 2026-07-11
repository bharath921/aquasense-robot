

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

const char* serverURL = "http://192.168.181.232:5000/data";

#define DHT_PIN 2       
#define DHT_TYPE DHT22   
#define SOIL_PIN A0      
#define TRIG_PIN 14     
#define ECHO_PIN 12     

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient wifiClient;
HTTPClient http;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("🌱 AquaSense ESP8266 Starting...");
  
  dht.begin();
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  connectToWiFi();
}

void connectToWiFi() {
  Serial.println("📶 Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi Connected!");
    Serial.print("📍 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("🌐 Server URL: ");
    Serial.println(serverURL);
    
    for(int i = 0; i < 3; i++) {
      digitalWrite(LED_BUILTIN, LOW);
      delay(200);
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);
    }
  } else {
    Serial.println("❌ WiFi Connection Failed!");
    Serial.println("Please check your WiFi credentials.");
  }
}

float readTemperature() {
  float temp = dht.readTemperature();
  if (isnan(temp)) {
    Serial.println("⚠️ Failed to read temperature!");
    return 25.0; 
  }
  return temp;
}

float readHumidity() {
  float humidity = dht.readHumidity();
  if (isnan(humidity)) {
    Serial.println("⚠️ Failed to read humidity!");
    return 50.0; 
  }
  return humidity;
}

float readSoilMoisture() {
  int rawValue = analogRead(SOIL_PIN);
  float moisture = map(rawValue, 1024, 0, 0, 100); 
  moisture = constrain(moisture, 0, 100);
  return moisture;
}

float readDistance() {
  
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  
  if (duration == 0) {
    return -1.0; 
  }
  
  float distance = (duration * 0.034) / 2; 
  return distance;
}

void sendDataToServer() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected. Reconnecting...");
    connectToWiFi();
    return;
  }
  
  // Read all sensors
  float temp = readTemperature();
  float humidity = readHumidity();
  float soilMoisture = readSoilMoisture();
  float distance = readDistance();
  
  // Display readings
  Serial.println("\n📊 === SENSOR READINGS ===");
  Serial.printf("🌡️ Temperature: %.2f °C\n", temp);
  Serial.printf("💧 Humidity: %.2f %%\n", humidity);
  Serial.printf("🌱 Soil Moisture: %.2f %%\n", soilMoisture);
  Serial.printf("📏 Distance: %.2f cm\n", distance);
  
  // Create JSON payload
  StaticJsonDocument<300> doc;
  doc["temp"] = temp;
  doc["humidity"] = humidity;
  doc["soil_moisture"] = soilMoisture;
  doc["distance"] = distance;
  doc["soil_type"] = "Sandy"; // You can change this or make it configurable
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📤 Sending JSON:");
  Serial.println(jsonString);
  
  // Send HTTP POST request
  http.begin(wifiClient, serverURL);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  Serial.printf("🌐 HTTP Response Code: %d\n", httpResponseCode);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Server Response:");
    Serial.println(response);
    
    // Parse response for crop prediction
    StaticJsonDocument<500> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error && responseDoc["status"] == "success") {
      Serial.println("\n🎯 === ANALYSIS RESULTS ===");
      if (responseDoc["analysis"]["predicted_crop"]) {
        Serial.printf("🌾 Recommended Crop: %s\n", responseDoc["analysis"]["predicted_crop"].as<const char*>());
        Serial.printf("💪 Confidence: %s\n", responseDoc["analysis"]["confidence"].as<const char*>());
        Serial.printf("💧 Water Status: %s\n", responseDoc["analysis"]["water_status"].as<const char*>());
        Serial.printf("🚿 Irrigation: %s\n", responseDoc["analysis"]["irrigation_needed"].as<const char*>());
      }
      
      // Blink LED to show success
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
      digitalWrite(LED_BUILTIN, HIGH);
    }
  } else {
    Serial.printf("❌ HTTP Error: %d\n", httpResponseCode);
    Serial.println("Check your server URL and network connection.");
  }
  
  http.end();
  Serial.println("=" * 50);
}

void loop() {
  Serial.println("\n🔄 Starting new reading cycle...");
  sendDataToServer();
  
  Serial.println("⏳ Waiting 10 seconds before next reading...");
  delay(10000); // Wait 10 seconds between readings
}