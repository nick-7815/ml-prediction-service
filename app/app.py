import os
import json
import pickle
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

MODEL_PATH = "/model/model.pkl"
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "10.10.10.101"),
    "dbname": os.environ.get("DB_NAME", "ml_predictions"),
    "user": os.environ.get("DB_USER", "ml_app"),
    "password": os.environ.get("DB_PASSWORD", "CHANGE_ME"),
    "sslmode": os.environ.get("DB_SSLMODE", "require"),
}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_version": "v1.0"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    if not data or "features" not in data:
        return jsonify({"error": "JSON must contain 'features' key"}), 400

    features = data["features"]
    if len(features) != 13:
        return jsonify({"error": "Expected exactly 13 features (Wine dataset)"}), 400

    prediction = int(model.predict([features])[0])

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO predictions (input_data, prediction, model_version) "
            "VALUES (%s, %s, %s)",
            (json.dumps(features), str(prediction), "v1.0"),
        )
        conn.commit()
        cur.close()
        conn.close()
        db_status = "saved"
    except Exception as e:
        db_status = "error: " + str(e)

    return jsonify({"prediction": prediction, "db_status": db_status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)