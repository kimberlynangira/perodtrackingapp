import joblib
import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np

MODEL_PATH = 'model/period_prediction_model.joblib' #Path to the saved model

def load_model():
        """Loads the trained machine learning model."""
        return joblib.load(MODEL_PATH)

def get_user_cycle_data(user_id, db_path='your_database.db'): # Default db_path added
        """Fetches historical cycle data for a given user from the database."""

        conn = sqlite3.connect(db_path)
        query = """
            SELECT
                c.cycle_start_date,
                c.cycle_end_date,
                u.user_id
            FROM
                Cycles c
            JOIN
                Users u ON c.user_id = u.user_id
            WHERE
                u.user_id = ?
            ORDER BY
                c.cycle_start_date
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df

def create_features(df):
        """Engineers features from the cycle data."""

        df['cycle_start_date'] = pd.to_datetime(df['cycle_start_date'])
        df = df.sort_values(by='cycle_start_date')
        df['days_to_next_period'] = (df['cycle_start_date'].shift(-1) - df['cycle_start_date']).dt.days
        df['cycle_length'] = df['days_to_next_period'].shift(1)

        df['prev_cycle_length_1'] = df['cycle_length'].shift(1)
        df['prev_cycle_length_2'] = df['cycle_length'].shift(2)
        df['month'] = df['cycle_start_date'].dt.month
        df['day_of_year'] = df['cycle_start_date'].dt.dayofyear

        df = df.dropna()
        return df

def predict_next_period(user_id):
        """Predicts the next period start date for a given user."""

        model = load_model()
        user_data = get_user_cycle_data(user_id)
        if user_data.empty:
            return None  # Or an appropriate message

        user_data_with_features = create_features(user_data)
        if user_data_with_features.empty:
            return None #Or appropriate message

        latest_cycle = user_data_with_features.iloc[[-1]]  # Get the latest cycle
        X = latest_cycle[['cycle_length', 'prev_cycle_length_1', 'prev_cycle_length_2', 'month', 'day_of_year']]

        next_period_days = model.predict(X)[0]
        next_period_date = latest_cycle['cycle_start_date'].iloc[0] + pd.Timedelta(days=np.round(next_period_days)) #Round the days to the nearest integer
        return next_period_date.strftime('%Y-%m-%d')  # Format the date
    
if __name__ == '__main__':
        # Example Usage (for testing):
        user_id = 1  # Replace with an actual user ID from your database
        next_period = predict_next_period(user_id)
        if next_period:
            print(f"Predicted next period for user {user_id}: {next_period}")
        else:
            print(f"Could not predict next period for user {user_id}")