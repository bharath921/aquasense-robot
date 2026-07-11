import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report

def train_and_compare():
    print("Loading dataset...")
    df = pd.read_csv('data_core.csv')
    
    # We discovered that only the first 99 rows represent the clean, non-noise dataset
    print(f"Total rows in CSV: {len(df)}")
    print("Filtering to the first 99 valid rows...")
    df_clean = df.iloc[:99].copy()
    
    # Prepare Label Encoders
    print("Encoding categorical fields...")
    le_soil = LabelEncoder()
    df_clean['Soil Type Encoded'] = le_soil.fit_transform(df_clean['Soil Type'])
    
    le_crop = LabelEncoder()
    df_clean['Crop Type Encoded'] = le_crop.fit_transform(df_clean['Crop Type'])
    
    # Define features and target
    features = ['Temparature', 'Humidity', 'Moisture', 'Soil Type Encoded']
    X = df_clean[features]
    y = df_clean['Crop Type Encoded']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define models
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=5, min_samples_split=2, random_state=42),
        "Support Vector Machine (SVM)": SVC(kernel='linear', C=1.0, probability=True, random_state=42),
        "K-Nearest Neighbors (KNN)": KNeighborsClassifier(n_neighbors=5),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42),
        "Multi-Layer Perceptron (MLP)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
    }
    
    best_model_name = None
    best_model = None
    best_score = -1
    model_results = {}
    
    # Evaluate using K-Fold Cross Validation
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    print("\n--- Model Evaluation (5-Fold Cross-Validation Accuracy) ---")
    for name, model in models.items():
        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
            mean_score = scores.mean()
            std_score = scores.std()
            model_results[name] = mean_score
            print(f"[*] {name}: Mean Accuracy = {mean_score:.4f} (+/- {std_score:.4f})")
            
            # Keep track of the best model based on CV score
            if mean_score > best_score:
                best_score = mean_score
                best_model_name = name
                best_model = model
        except Exception as e:
            print(f"[ERROR] Failed to train {name}: {e}")
            
    print(f"\nBest Model: {best_model_name} with CV Accuracy of {best_score:.4f}")
    
    # Train the best model on full training split and evaluate on test split
    print(f"\n--- Testing Best Model ({best_model_name}) on Holdout Test Set ---")
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"Test Set Accuracy: {test_acc:.4f}")
    
    # Re-fit on all 99 valid rows to maximize learning from the entire clean dataset
    print(f"\nRe-fitting {best_model_name} on the entire clean dataset...")
    best_model.fit(X, y)
    
    # Save best model and label encoders
    print("\nSaving best model and encoders...")
    with open('crop_predictor.pkl', 'wb') as f:
        pickle.dump(best_model, f)
        
    with open('soil_encoder.pkl', 'wb') as f:
        pickle.dump(le_soil, f)
        
    with open('crop_encoder.pkl', 'wb') as f:
        pickle.dump(le_crop, f)
        
    print("Model and Encoders saved successfully!")
    
    # Print label classes for debugging
    print("\nSoil Type Classes:", list(le_soil.classes_))
    print("Crop Type Classes:", list(le_crop.classes_))

if __name__ == '__main__':
    train_and_compare()
