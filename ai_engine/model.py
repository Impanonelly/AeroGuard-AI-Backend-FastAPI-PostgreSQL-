import os

# Determine the absolute path to the pre-trained model file
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_model.pkl")

# We use a global variable to store the model in memory.
# This prevents reloading the heavy .pkl file on every single API request,
# ensuring 0-millisecond latency during predictions.
_model = None

def get_ai_model():
    """
    Lazy loads the Scikit-Learn RandomForest model into memory.
    If it's already loaded, it just returns the cached instance.
    """
    global _model
    
    # Lazy import so the server doesn't crash if pip install is still running
    import joblib
    
    if _model is not None:
        return _model
        
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Critial Error: AI fatigue_model.pkl not found at {MODEL_PATH}. "
            "Please run 'python ai_engine/train.py' first to compile the neural engine."
        )
        
    print(f"[*] Booting up AeroGuard AI Machine Learning Engine from {MODEL_PATH}")
    _model = joblib.load(MODEL_PATH)
    return _model

def predict_risk(sleep_hours: float, duty_hours: float, stress_level: float) -> str:
    """
    Passes the pilot's biometric data through the Random Forest Classifier
    to generate an instantaneous Risk Level Prediction.
    """
    model = get_ai_model()
    
    # The model expects a 2D array: [[sleep, duty, stress]]
    # It returns an array of predictions, we grab the first one.
    prediction = model.predict([[sleep_hours, duty_hours, stress_level]])
    
    # Return the string classification (LOW, MEDIUM, HIGH)
    return str(prediction[0])
