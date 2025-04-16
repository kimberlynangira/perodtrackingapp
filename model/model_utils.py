import joblib
import numpy as np
import pandas as pd
import logging


# Configure logging (if not already configured)
logging.basicConfig(level=logging.DEBUG)

def load_model(model_path):
    """Loads the trained machine learning model."""
    try:
        model = joblib.load(model_path)
        print(model)
        logging.info(f"Model loaded successfully from {model_path}")
        return model
    except FileNotFoundError:
        logging.error(f"Model file not found at {model_path}")
        raise  # Re-raise the exception to be handled by the caller
    except Exception as e:
        logging.exception(f"Error loading model from {model_path}: {e}")
        raise  # Re-raise for the caller to handle

def predict_cycle_length(model, data):
    """
    Predicts the cycle length using the loaded model.

    Args:
        model: The loaded machine learning model.
        data: A dictionary containing the input features.

    Returns:
        The predicted cycle length, or None on error.
    """
    try:
        logging.debug(f"Input data: {data}")  # Log the input data
        # Convert data to DataFrame
        data_df = pd.DataFrame([data])

        # Ensure the order of columns in data_df matches the order
        # the model was trained on.
        expected_columns = [
            'user_id_encoded', 'cycle_start_month', 'period_duration',
            'days_until_ovulation', 'flow_Heavy', 'flow_Light',
            'flow_Medium', 'symptom_acne', 'symptom_mood swings',
            'symptom_fatigue', 'symptom_cramps', 'symptom_headache',
            'symptom_breast tenderness', 'symptom_bloating',
            'symptom_insomnia', 'mean_cycle_length',
            'std_cycle_length', 'avg_period_duration'
        ]

        # Check for missing columns
        missing_columns = [col for col in expected_columns if col not in data_df.columns]
        if missing_columns:
            error_message = f"Missing columns: {', '.join(missing_columns)}"
            logging.error(error_message)
            raise ValueError(error_message)

        data_df = data_df[expected_columns]  # Order the columns

        # Check for empty DataFrame
        if data_df.empty:
            error_message = "DataFrame is empty.  No data provided for prediction."
            logging.error(error_message)
            raise ValueError(error_message)

        # Check for NaN values in the DataFrame
        if data_df.isnull().values.any():
            error_message = "DataFrame contains NaN values.  Prediction cannot be performed."
            logging.error(error_message)
            raise ValueError(error_message)

        prediction = model.predict(data_df)[0]
        logging.debug(f" Prediction: {prediction}")
        return float(prediction)
    except (KeyError, ValueError, TypeError) as e:
        # Log the specific error
        logging.error(f"Error during prediction: {e}")
        return None  # Return None on error
    except Exception as e:
        # Catch any other unexpected exceptions
        logging.exception(f"Unexpected error during prediction: {e}")
        return None
