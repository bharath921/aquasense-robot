import app_fixed

def test_pipeline():
    print("Testing ML crop prediction model in isolation...")
    
    # Test cases representing typical conditions
    test_cases = [
        {"temp": 26.0, "humidity": 52.0, "moisture": 38.0, "soil_type": "Sandy", "expected_desc": "Should predict crop for Sandy soil"},
        {"temp": 29.0, "humidity": 52.0, "moisture": 45.0, "soil_type": "Loamy", "expected_desc": "Should predict crop for Loamy soil"},
        {"temp": 34.0, "humidity": 65.0, "moisture": 62.0, "soil_type": "Black", "expected_desc": "Should predict crop for Black soil"},
        {"temp": 12.0, "humidity": 30.0, "moisture": 10.0, "soil_type": "UnknownSoil", "expected_desc": "Should fallback gracefully for unknown soil type"}
    ]
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\nTest Case #{i}: {tc['expected_desc']}")
        print(f"Inputs: Temp={tc['temp']}, Humid={tc['humidity']}, Moist={tc['moisture']}, Soil={tc['soil_type']}")
        
        crop, confidence = app_fixed.predict_crop(
            tc['temp'], tc['humidity'], tc['moisture'], tc['soil_type']
        )
        
        print(f"Result -> Predicted Crop: {crop}, Confidence: {confidence}")
        
        # Validation checks
        assert crop is not None, "Predicted crop should not be None"
        assert len(crop) > 0, "Predicted crop should be a non-empty string"
        assert confidence is not None, "Confidence should not be None"
        
    print("\nAll unit tests passed successfully!")

if __name__ == '__main__':
    test_pipeline()
