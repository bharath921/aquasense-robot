"""Audit the crop dataset and compare classifiers without writing model files."""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier


FEATURES = ["Temparature", "Humidity", "Moisture", "Soil Type"]
TARGET = "Crop Type"


def audit(data, name):
    print(f"\n{name}: {len(data)} rows, {data.duplicated().sum()} duplicate rows")
    print("Missing values:", data.isna().sum().to_dict())
    print("Crop counts:", data[TARGET].value_counts().to_dict())
    crop_counts = data.groupby(FEATURES, dropna=False)[TARGET].nunique()
    print(f"Identical input combinations with conflicting crop labels: {(crop_counts > 1).sum()}")


def main():
    data = pd.read_csv(Path(__file__).with_name("data_core.csv"))
    reference = data.iloc[:99]
    audit(reference, "Existing training subset")
    audit(data.iloc[99:], "Remaining records")

    features = reference[FEATURES]
    encoder = LabelEncoder()
    labels = encoder.fit_transform(reference[TARGET])
    groups = features.groupby(FEATURES, dropna=False).ngroup()
    preprocessing = ColumnTransformer([
        ("soil", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Soil Type"]),
    ], remainder="passthrough")
    candidates = {
        "Random Forest": (RandomForestClassifier(n_estimators=100, random_state=42), [3, 6, None]),
        "XGBoost": (XGBClassifier(n_estimators=100, n_jobs=1, random_state=42), [2, 4, 6]),
        "Extra Trees": (ExtraTreesClassifier(n_estimators=100, random_state=42), [3, 6, None]),
        "Gradient Boosting": (GradientBoostingClassifier(random_state=42), [1, 2, 3]),
        "Decision Tree": (DecisionTreeClassifier(random_state=42), [3, 6, None]),
    }
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(outer.split(features, labels, groups))
    inner_folds = []
    for train, _ in folds:
        training_labels = labels[train]
        training_features = features.iloc[train]
        training_groups = groups.iloc[train]
        n_splits = min(3, pd.Series(training_labels).value_counts().min())
        for seed in range(43, 143):
            inner = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
            splits = list(inner.split(training_features, training_labels, training_groups))
            if all(len(set(training_labels[fit])) == len(encoder.classes_) for fit, _ in splits):
                inner_folds.append(splits)
                break
        else:
            raise ValueError("Could not split training groups while retaining all crops in each fit")
    predictions = {}

    print("\nOut-of-fold results, with tree depth tuned inside each training fold")
    for name, (classifier, depths) in candidates.items():
        pipeline = make_pipeline(preprocessing, classifier)
        parameter = f"{type(classifier).__name__.lower()}__max_depth"
        out_of_fold = labels.copy()
        for (train, test), splits in zip(folds, inner_folds):
            search = GridSearchCV(
                pipeline, {parameter: depths}, scoring="f1_macro", cv=splits, error_score="raise"
            )
            search.fit(features.iloc[train], labels[train])
            out_of_fold[test] = search.predict(features.iloc[test])
        predictions[name] = out_of_fold
        print(f"{name}: accuracy {accuracy_score(labels, out_of_fold):.2%}, "
              f"macro F1 {f1_score(labels, out_of_fold, average='macro'):.2%}")

    best = max(predictions, key=lambda name: f1_score(labels, predictions[name], average="macro"))
    print(f"\n{best} per-crop results")
    print(classification_report(labels, predictions[best], target_names=encoder.classes_, zero_division=0))
    print("Confusion matrix (rows actual, columns predicted)")
    print(pd.DataFrame(confusion_matrix(labels, predictions[best]),
                       index=encoder.classes_, columns=encoder.classes_).to_string())


if __name__ == "__main__":
    main()
