import argparse
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix,
)

def train_and_compare(evaluate_only=False):
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
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=5, min_samples_split=2, random_state=42),
        "Support Vector Machine (SVM)": SVC(kernel="linear", C=1.0, probability=True, random_state=42),
        "K-Nearest Neighbors (KNN)": KNeighborsClassifier(n_neighbors=5),
        "XGBoost": XGBClassifier(eval_metric="mlogloss", random_state=42, n_jobs=1),
        "Multi-Layer Perceptron (MLP)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42),
    }

    best_model_name = None
    best_model = None
    best_score = -1
    cv = StratifiedKFold(n_splits=min(5, y_train.value_counts().min()), shuffle=True, random_state=42)

    print(f"\n--- Model selection ({cv.n_splits}-fold training CV, macro F1) ---")
    for name, model in models.items():
        try:
            scores = cross_val_score(
                model, X_train, y_train, cv=cv, scoring="f1_macro", error_score="raise"
            )
        except Exception as error:
            print(f"[ERROR] Failed to train {name}: {error}")
            continue
        mean_score = scores.mean()
        print(f"[*] {name}: Mean macro F1 = {mean_score:.4f} (+/- {scores.std():.4f})")
        if mean_score > best_score:
            best_score = mean_score
            best_model_name = name
            best_model = model

    if best_model is None:
        raise RuntimeError("All candidate models failed cross-validation")
    print(f"\nBest model: {best_model_name} (CV macro F1 {best_score:.4f})")
    print(f"\n--- Testing Best Model ({best_model_name}) on Holdout Test Set ---")
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    print(f"Train rows: {len(X_train)} | Test rows: {len(X_test)}")
    print(f"Majority-class baseline accuracy: {baseline.score(X_test, y_test):.4f}")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred):.4f}")
    labels = list(range(len(le_crop.classes_)))
    print(classification_report(
        y_test, y_pred, labels=labels, target_names=le_crop.classes_, digits=4, zero_division=0
    ))
    print("Confusion matrix (rows: actual, columns: predicted)")
    print(pd.DataFrame(
        confusion_matrix(y_test, y_pred, labels=labels),
        index=le_crop.classes_, columns=le_crop.classes_,
    ).to_string())

    if evaluate_only:
        return
    
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluate-only", action="store_true", help="Report metrics without replacing model files.")
    train_and_compare(evaluate_only=parser.parse_args().evaluate_only)
