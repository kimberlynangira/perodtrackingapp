# train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from io import StringIO
import numpy as np

data = """
user_id,cycle_start,cycle_end,cycle_length,ovulation_day,flow_level,symptoms
user_01,2024-10-01,2024-10-06,31,2024-10-16,Medium,"acne, mood swings, fatigue"
user_01,2024-11-01,2024-11-06,32,2024-11-17,Medium,"cramps, fatigue, headache"
user_01,2024-12-03,2024-12-08,33,2024-12-19,Medium,"fatigue, breast tenderness"
user_01,2025-01-05,2025-01-09,34,2025-01-22,Heavy,fatigue
user_01,2025-02-08,2025-02-12,34,2025-02-25,Medium,"fatigue, acne"
user_01,2025-03-14,2025-03-19,32,2025-03-30,Medium,"headache, mood swings, breast tenderness"
user_02,2024-10-01,2024-10-03,21,2024-10-11,Heavy,breast tenderness
user_02,2024-10-22,2024-10-27,25,2024-11-03,Medium,insomnia
user_02,2024-11-16,2024-11-22,23,2024-11-27,Medium,"fatigue, acne"
user_02,2024-12-09,2024-12-12,25,2024-12-21,Medium,acne
user_02,2025-01-03,2025-01-06,24,2025-01-15,Medium,cramps
user_02,2025-01-27,2025-01-31,23,2025-02-07,Medium,"acne, bloating, mood swings"
user_03,2024-10-01,2024-10-04,25,2024-10-13,Medium,"insomnia, acne, mood swings"
user_03,2024-10-26,2024-11-01,31,2024-11-10,Medium,"acne, bloating"
user_03,2024-11-26,2024-12-02,25,2024-12-08,Heavy,insomnia
user_03,2024-12-21,2024-12-26,26,2025-01-03,Medium,"breast tenderness, headache, insomnia"
user_03,2025-01-16,2025-01-21,26,2025-01-29,Heavy,"mood swings, headache"
user_03,2025-02-11,2025-02-14,24,2025-02-23,Light,"fatigue, insomnia, mood swings"
user_04,2024-10-01,2024-10-04,30,2024-10-16,Heavy,"fatigue, mood swings"
user_04,2024-10-31,2024-11-02,34,2024-11-17,Heavy,cramps
user_04,2024-12-04,2024-12-07,22,2024-12-15,Medium,"bloating, cramps"
user_04,2024-12-26,2024-12-29,32,2025-01-11,Light,"headache, bloating, breast tenderness"
user_04,2025-01-27,2025-02-01,32,2025-02-12,Heavy,bloating
user_04,2025-02-28,2025-03-06,32,2025-03-16,Medium,"fatigue, acne, bloating"
user_05,2024-10-01,2024-10-07,22,2024-10-12,Heavy,"cramps, breast tenderness, acne"
user_05,2024-10-23,2024-10-29,32,2024-11-08,Medium,cramps
user_05,2024-11-24,2024-11-27,23,2024-12-05,Light,"cramps, acne, fatigue"
user_05,2024-12-17,2024-12-23,31,2025-01-01,Heavy,cramps
user_05,2025-01-17,2025-01-21,24,2025-01-29,Medium,"insomnia, breast tenderness"
user_05,2025-02-10,2025-02-13,33,2025-02-26,Light,"fatigue, cramps, insomnia"
user_06,2024-10-01,2024-10-05,29,2024-10-15,Medium,"fatigue, mood swings, breast tenderness"
user_06,2024-10-30,2024-11-04,28,2024-11-13,Light,headache
user_06,2024-11-27,2024-12-01,29,2024-12-11,Heavy,insomnia
user_06,2024-12-26,2024-12-30,26,2025-01-08,Light,bloating
user_06,2025-01-21,2025-01-27,29,2025-02-04,Medium,"insomnia, headache, mood swings"
user_06,2025-02-19,2025-02-21,28,2025-03-05,Light,"fatigue, insomnia, cramps"
user_07,2024-10-01,2024-10-04,25,2024-10-13,Medium,"insomnia, headache"
user_07,2024-10-26,2024-10-30,23,2024-11-06,Light,headache
user_07,2024-11-18,2024-11-24,23,2024-11-29,Light,cramps
user_07,2024-12-11,2024-12-16,24,2024-12-23,Light,"mood swings, headache"
user_07,2025-01-04,2025-01-07,23,2025-01-15,Medium,bloating
user_07,2025-01-27,2025-01-29,25,2025-02-08,Heavy,"headache, cramps"
user_08,2024-10-01,2024-10-07,21,2024-10-11,Medium,"breast tenderness, insomnia, headache"
user_08,2024-10-22,2024-10-26,22,2024-11-02,Medium,bloating
user_08,2024-11-13,2024-11-16,25,2024-11-25,Medium,"acne, cramps, headache"
user_08,2024-12-08,2024-12-12,23,2024-12-19,Light,headache
user_08,2024-12-31,2025-01-04,24,2025-01-12,Light,"cramps, insomnia"
user_08,2025-01-24,2025-01-29,25,2025-02-05,Heavy,insomnia
user_09,2024-10-01,2024-10-03,31,2024-10-16,Light,"acne, fatigue"
user_09,2024-11-01,2024-11-05,33,2024-11-17,Light,breast tenderness
user_09,2024-12-04,2024-12-10,29,2024-12-18,Medium,"cramps, headache, breast tenderness"
user_09,2025-01-02,2025-01-08,22,2025-01-13,Medium,"mood swings, bloating"
user_09,2025-01-24,2025-01-29,25,2025-02-05,Heavy,bloating
user_09,2025-02-18,2025-02-20,28,2025-03-04,Heavy,mood swings
user_10,2024-10-01,2024-10-06,24,2024-10-13,Medium,"headache, bloating"
user_10,2024-10-25,2024-10-29,21,2024-11-04,Heavy,"mood swings, cramps"
user_10,2024-11-15,2024-11-20,22,2024-11-26,Medium,acne
user_10,2024-12-07,2024-12-10,21,2024-12-17,Heavy,"insomnia, mood swings"
user_10,2024-12-28,2024-12-30,21,2025-01-07,Heavy,"mood swings, acne, cramps"
user_10,2025-01-18,2025-01-20,22,2025-01-29,Heavy,"mood swings, bloating, cramps"
"""

def prepare_data(data):
    df = pd.read_csv(StringIO(data))
    df['cycle_start'] = pd.to_datetime(df['cycle_start'])
    df['cycle_end'] = pd.to_datetime(df['cycle_end'])
    df['ovulation_day'] = pd.to_datetime(df['ovulation_day'])
    df['period_duration'] = (df['cycle_end'] - df['cycle_start']).dt.days + 1
    df['days_until_ovulation'] = (df['ovulation_day'] - df['cycle_start']).dt.days
    df['cycle_start_month'] = df['cycle_start'].dt.month
    df = pd.get_dummies(df, columns=['flow_level'], prefix='flow')
    df['symptoms'] = df['symptoms'].fillna('')
    common_symptoms = ['acne', 'mood swings', 'fatigue', 'cramps', 'headache', 'breast tenderness', 'bloating', 'insomnia']
    for symptom in common_symptoms:
        df[f'symptom_{symptom}'] = df['symptoms'].apply(lambda x: 1 if symptom in x else 0)
    df = df.drop(columns=['symptoms'])
    user_data = df.groupby('user_id').agg(
        mean_cycle_length=('cycle_length', 'mean'),
        std_cycle_length=('cycle_length', 'std'),
        avg_period_duration=('period_duration', 'mean')
    ).reset_index()
    df = pd.merge(df, user_data, on='user_id', how='left')
    df['std_cycle_length'] = df['std_cycle_length'].fillna(0)
    from sklearn.preprocessing import LabelEncoder
    user_encoder = LabelEncoder()
    df['user_id_encoded'] = user_encoder.fit_transform(df['user_id'])
    selected_columns = ['user_id_encoded', 'cycle_start_month', 'cycle_length', 'period_duration', 'days_until_ovulation',
                        'flow_Heavy', 'flow_Light', 'flow_Medium',
                        'symptom_acne', 'symptom_mood swings', 'symptom_fatigue', 'symptom_cramps', 'symptom_headache',
                        'symptom_breast tenderness', 'symptom_bloating', 'symptom_insomnia',
                        'mean_cycle_length', 'std_cycle_length', 'avg_period_duration']
    df = df[selected_columns].copy()
    return df

# Prepare the data
prepared_df = prepare_data(data)

# Define features (X) and target (y)
X = prepared_df.drop('cycle_length', axis=1)
y = prepared_df['cycle_length']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)

# Train the model
rf_model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = rf_model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print("Model Evaluation:")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
print(f"R-squared (R2): {r2:.2f}")

# Save the trained model
model_filename = 'cycle_length_rf_model.joblib'
joblib.dump(rf_model, model_filename)
print(f"\nTrained model saved as {model_filename}")