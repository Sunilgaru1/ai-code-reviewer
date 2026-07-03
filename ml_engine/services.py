import joblib
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# 1. Load the model into memory ONE TIME when the Django server starts
model_path = os.path.join(settings.BASE_DIR, 'ai_reviewer_model.pkl')
try:
    model = joblib.load(model_path)
    logger.info("AI Brain loaded successfully.")
except Exception as e:
    logger.error(f"Could not load AI model: {e}")
    model = None

# 2. Expose a simple function for our webhooks app to use
def get_maintainability_score(functions, classes, loops, complexity):
    if model is None:
        logger.warning("AI Model is missing. Returning default score.")
        return 0.0
    
    # Format the data exactly how scikit-learn expects it
    features = [[functions, classes, loops, complexity]]
    
    # Predict and return the score
    prediction = model.predict(features)
    return round(prediction[0], 2)