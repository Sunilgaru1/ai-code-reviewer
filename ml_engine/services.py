import joblib
import os
import pandas as pd 
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

model_path = os.path.join(settings.BASE_DIR, 'ai_reviewer_model.pkl')
try:
    model = joblib.load(model_path)
    logger.info("AI Brain loaded successfully.")
except Exception as e:
    logger.error(f"Could not load AI model: {e}")
    model = None

def get_maintainability_score(functions, classes, loops, complexity):
    if model is None:
        logger.warning("AI Model is missing. Returning default score.")
        return 0.0
    
    # Create a DataFrame with the exact column names used during training
    features = pd.DataFrame([{
        'functions': functions,
        'classes': classes,
        'loops': loops,
        'complexity': complexity
    }])
    
    # Predict using the DataFrame to eliminate the feature names warning
    prediction = model.predict(features)
    return round(prediction[0], 2)