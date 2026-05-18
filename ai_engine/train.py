import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Ensure the models directory exists
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_synthetic_data(num_samples=5000):
    """
    Generate synthetic pilot aviation data to train the AI model.
    Features: Sleep (0-12 hrs), Duty (0-16 hrs), Stress (0-10)
    Label: Risk Status (LOW, MEDIUM, HIGH)
    """
    print(f"[*] Generating {num_samples} synthetic pilot health records...")
    np.random.seed(42)  # For reproducible results
    
    # 1. Generate realistic input features
    # Sleep usually centers around 7 hours, bounded 0-12
    sleep_hours = np.clip(np.random.normal(loc=7.0, scale=2.0, size=num_samples), 0, 12)
    
    # Duty hours usually center around 8 hours, bounded 0-16
    duty_hours = np.clip(np.random.normal(loc=8.0, scale=3.0, size=num_samples), 0, 16)
    
    # Stress level (0-10 bounds)
    stress_level = np.clip(np.random.normal(loc=4.0, scale=2.5, size=num_samples), 0, 10)
    
    # 2. Build mathematical risk simulation to label the training data
    # (Sleep deficit is severely penalized, long duties add fatigue, high stress adds cognitive load)
    # This formula creates the "Ground Truth" that the ML model will learn to mimic.
    sleep_deficit = (8.0 - sleep_hours)
    sleep_deficit = np.where(sleep_deficit < 0, 0, sleep_deficit) # No bonus for >8 hrs sleep
    
    synthetic_risk_scores = (sleep_deficit * 2.5) + (duty_hours * 1.5) + (stress_level * 1.8)
    
    # 3. Add random real-world "noise" so the ML model has to work hard to generalize 
    # instead of just learning a perfect linear formula.
    noise = np.random.normal(0, 3.0, num_samples)
    final_scores = synthetic_risk_scores + noise
    
    # 4. Classify labels based on rigorous safety thresholds
    labels = []
    for score in final_scores:
        if score < 12.0:
            labels.append("LOW")
        elif score < 24.0:
            labels.append("MEDIUM")
        else:
            labels.append("HIGH")
            
    df = pd.DataFrame({
        "sleep_hours": sleep_hours,
        "duty_hours": duty_hours,
        "stress_level": stress_level,
        "risk_level": labels
    })
    
    return df

def train_and_export_model():
    """Trains the RandomForest AI and saves it to a .pkl file."""
    print("[*] Initializing AeroGuard AI Training Pipeline...")
    
    # 1. Acquire Data
    df = generate_synthetic_data(10000)
    
    X = df[['sleep_hours', 'duty_hours', 'stress_level']]
    y = df['risk_level']
    
    # 2. Split Data (80% training, 20% validation)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 3. Initialize Scikit-Learn RandomForest Component
    # We use 100 decision trees to ensure high fidelity predictions
    print("[*] Training Random Forest Neural Matrix (n_estimators=100)...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    
    # 4. Train the AI Model
    clf.fit(X_train, y_train)
    print("[+] Model training completed successfully.")
    
    # 5. Evaluate Accuracy
    predictions = clf.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"\n[+] AI Model Accuracy Rating: {accuracy * 100:.2f}%")
    print("\n--- Detailed Classification Report ---")
    print(classification_report(y_test, predictions, zero_division=0))
    
    # 6. Export to PKL File for FastAPI Production Injection
    model_path = os.path.join(MODEL_DIR, "fatigue_model.pkl")
    joblib.dump(clf, model_path)
    print(f"\n[+] Production AI Engine safely exported to: {model_path}")
    print("[*] AeroGuard AI is ready for deployment in FastAPI.")

if __name__ == "__main__":
    train_and_export_model()
