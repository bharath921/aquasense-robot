"""
Enhanced test script to demonstrate distance-integrated crop recommendations
"""
import requests
import json
import time

test_scenarios = [
    {
        "name": "Shallow Water Table Area",
        "data": {
            "temperature": 28.0,
            "humidity": 75.0,
            "moisture": 65.0,
            "distance": 8.5, 
            "soil_type": "clay"
        },
        "description": "High water table - expect rice/sugarcane recommendation"
    },
    {
        "name": "Moderate Water Depth Area", 
        "data": {
            "temperature": 25.0,
            "humidity": 55.0,
            "moisture": 45.0,
            "distance": 22.0,  
            "soil_type": "loamy"
        },
        "description": "Moderate water access - expect wheat/maize recommendation"
    },
    {
        "name": "Deep Water Table Area",
        "data": {
            "temperature": 32.0,
            "humidity": 40.0,
            "moisture": 25.0,
            "distance": 45.0, 
            "soil_type": "sandy"
        },
        "description": "Deep water table - expect drought-resistant crops like bajra"
    }
]

print("🌊 Testing Distance-Integrated Crop Recommendations")
print("=" * 60)

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n📍 Test Scenario {i}: {scenario['name']}")
    print(f"   {scenario['description']}")
    print(f"   🌊 Water table depth: {scenario['data']['distance']}cm")
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/data',
            headers={'Content-Type': 'application/json'},
            json=scenario['data'],
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', {})
            
            print(f"   ✅ Recommended Crop: {analysis.get('predicted_crop', 'Unknown')}")
            print(f"   🎯 Confidence: {analysis.get('confidence', 'Unknown')}")
            print(f"   💧 Water Status: {analysis.get('water_status', 'Unknown')}")
            print(f"   🚿 Irrigation: {analysis.get('irrigation_needed', 'Unknown')}")
            print(f"   🌊 Water Table Analysis: {analysis.get('water_table_estimate', 'Unknown')}")
            
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(1)

print("\n" + "=" * 60)
print("🌐 Open your browser to see detailed analysis:")
print("   http://127.0.0.1:5000")
print("\n🌾 Notice how different water table depths affect:")
print("   • Crop recommendations (Rice for shallow, Bajra for deep)")
print("   • Irrigation requirements (Less for shallow water table)")
print("   • Water table analysis (Depth-based insights)")
print("   • Care tips specific to water availability")

print("\n🔄 Refresh your dashboard to see the latest analysis!")