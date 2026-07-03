import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def generate_synthetic_data(num_samples=1000):
    logging.info("Generating synthetic training data...")
    np.random.seed(42) 

    functions = np.random.randint(0, 15, num_samples)
    classes = np.random.randint(0, 5, num_samples)
    loops = np.random.randint(0, 10, num_samples)
    complexity = np.random.randint(1, 25, num_samples)

    base_score = 100
    penalties = (complexity * 2.5) + (loops * 1.5) + (functions * 0.5)
    scores = base_score - penalties
    
    noise = np.random.normal(0, 5, num_samples)
    maintainability = np.clip(scores + noise, 0, 100) 

    return pd.DataFrame({
        'functions': functions,
        'classes': classes,
        'loops': loops,
        'complexity': complexity,
        'maintainability': maintainability
    })

def train_and_save_model():
    df = generate_synthetic_data()
    
    X = df[['functions', 'classes', 'loops', 'complexity']]
    y = df['maintainability']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    logging.info("Training the Random Forest model...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    logging.info(f"Model Accuracy (R^2 Score): {accuracy * 100:.2f}%")

    filename = 'ai_reviewer_model.pkl'
    joblib.dump(model, filename)
    logging.info(f"Successfully saved trained model to: {filename}")

if __name__ == "__main__":
    train_and_save_model()