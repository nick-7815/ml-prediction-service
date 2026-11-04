from flask import Flask, request, jsonify, Response
import psycopg2, json, os, pickle, time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Загрузка модели
MODEL_PATH = os.getenv("MODEL_PATH", "model/model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Метрики
PREDICTIONS_TOTAL = Counter(
    "ml_predictions_total", "Total number of predictions",
    ["model_version", "predicted_class"]
)
PREDICTION_LATENCY = Histogram(
    "ml_prediction_latency_seconds", "Prediction latency in seconds"
)
DB_ERRORS_TOTAL = Counter("ml_db_errors_total", "Total number of DB write errors")
MODEL_INFO = Gauge(
    "ml_model_info", "Model info", ["version"]
)
MODEL_INFO.labels(version="v1.0").set(1)

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "10.10.10.101"),
        dbname=os.getenv("DB_NAME", "ml_predictions"),
        user=os.getenv("DB_USER", "ml_app"),
        password=os.getenv("DB_PASSWORD", "StrongPassword"),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/predict", methods=["POST"])
def predict():
    start = time.time()
    data = request.get_json(force=True)
    features = data.get("features", [])
    if not features:
        return jsonify({"error": "No features provided"}), 400

    pred = model.predict([features])[0]
    proba = max(model.predict_proba([features])[0])
    result = {"class": int(pred), "probability": float(proba)}

    PREDICTION_LATENCY.observe(time.time() - start)
    PREDICTIONS_TOTAL.labels(model_version="v1.0", predicted_class=str(pred)).inc()

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO predictions (input_data, prediction, model_version) VALUES (%s, %s, %s)",
            (json.dumps({"features": features}), json.dumps(result), "v1.0")
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        DB_ERRORS_TOTAL.inc()
        app.logger.error(f"DB error: {e}")

    return jsonify(result)

@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
