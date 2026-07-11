/*
  Simple ESP8266 Connection Test
  Upload this minimal code first to verify connection
*/

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("ESP8266 Connection Test");
  Serial.println("If you see this message, upload is working!");
  
  // Initialize built-in LED
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // Blink LED to show it's working
  digitalWrite(LED_BUILTIN, LOW);   // Turn LED on (LOW = on for ESP8266)
  delay(1000);
  digitalWrite(LED_BUILTIN, HIGH);  // Turn LED off
  delay(1000);
  
  // Print message every 2 seconds
  Serial.println("ESP8266 is working! Time: " + String(millis()));
}