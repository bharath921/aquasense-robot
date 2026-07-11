
"""
Test script to send sample data and see crop details
"""
import requests
import json

test_data = {
    "temperature": 25.5,
    "humidity": 45.0,
    "moisture": 30.0,
    "distance": 15.0,
    "soil_type": "sandy"
}

print("🧪 Testing AquaSense Crop Details System")
print("="*50)

try:
    response = requests.post(
        'http://127.0.0.1:5000/data',
        headers={'Content-Type': 'application/json'},
        json=test_data,
        timeout=5
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Test data sent successfully!")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        print("\n🌐 Now open your browser to see detailed crop information:")
        print("   http://127.0.0.1:5000")
        print("\n🌾 The dashboard will show:")
        print("   • Recommended crop for your conditions")
        print("   • Detailed growing instructions")
        print("   • Optimal conditions needed")
        print("   • Care tips and best practices")
        print("   • Market value and nutrition info")
        
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    print("Make sure the Flask server is running!")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "="*50)
print("🔄 Refresh your browser to see the updated crop details!")