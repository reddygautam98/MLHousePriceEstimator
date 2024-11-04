import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import numpy as np
from flask import Flask, request, jsonify
import mlflow
import mlflow.sklearn

# Load data
data = pd.read_csv(r'C:\Users\reddy\Downloads\price.py\pricepridiction\house_prices.csv')  # Update this with your actual CSV path

# Handle missing values by filling them with the median
data.fillna(data.median(), inplace=True)

# Scale numerical features
scaler = StandardScaler()
num_features = ['sqft_living', 'sqft_lot', 'floors', 'bedrooms', 'bathrooms']
missing_features = [feature for feature in num_features if feature not in data.columns]

if missing_features:
    raise ValueError(f"Missing features in dataset: {missing_features}")

data[num_features] = scaler.fit_transform(data[num_features])

# Encode categorical features if present
label_encoder = LabelEncoder()
for col in ['waterfront', 'view']:
    if col in data.columns:
        data[col] = label_encoder.fit_transform(data[col])
    else:
        raise ValueError(f"Required categorical column '{col}' is missing.")

# Check if target variable 'price' is present
if 'price' not in data.columns:
    raise ValueError("Target column 'price' is missing.")

# Split data into features and target
X = data.drop('price', axis=1)
y = data['price']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Predict and evaluate
predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)
print(f"Mean Squared Error: {mse}")

# Save the trained model
joblib.dump(model, "house_price_model.pkl")

# Log parameters and metrics with MLflow
mlflow.start_run()
mlflow.log_param("model_type", "LinearRegression")
mlflow.log_metric("MSE", mse)
mlflow.sklearn.log_model(model, "model")

# Define an input example for MLflow model signature
input_example = {
    "sqft_living": 2000,
    "sqft_lot": 5000,
    "floors": 2,
    "bedrooms": 3,
    "bathrooms": 2,
    "waterfront": 0,  # Assuming 0 for 'no waterfront'
    "view": 1         # Assuming 1 for some view
}
mlflow.sklearn.log_model(model, "model", input_example=input_example)
mlflow.end_run()
print("Model logged successfully with MLflow.")

# Initialize Flask application
app = Flask("HouseHub")

# Load the model
try:
    model = joblib.load("house_price_model.pkl")
except Exception as e:
    print(f"Error loading model: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)  # Get the JSON data from the request
        features = data['features']  # Extract features from the input JSON

        # Validate that all required features are present
        required_features = ['sqft_living', 'sqft_lot', 'floors', 'bedrooms', 'bathrooms', 'waterfront', 'view']
        for feature in required_features:
            if feature not in features:
                return jsonify({'error': f'Missing feature in input data: {feature}'}), 400

        # Convert the features into the appropriate format for prediction
        features_array = np.array([
            features['sqft_living'],
            features['sqft_lot'],
            features['floors'],
            features['bedrooms'],
            features['bathrooms'],
            features['waterfront'],
            features['view']
        ]).reshape(1, -1)  # Reshape to 2D array

        # Make prediction
        prediction = model.predict(features_array)
        return jsonify({'prediction': prediction.tolist()})

    except KeyError as e:
        return jsonify({'error': f'Missing feature in input data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app (uncomment when running the script directly)
# if __name__ == "__main__":
#     app.run(debug=True)
