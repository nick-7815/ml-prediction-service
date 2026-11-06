from flask import Flask, request, jsonify, Response
import psycopg2
import json
import os
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Метрики
LOG_REQUESTS_TOTAL = Counter(
    "logger_requests_total", "Total log requests", ["status"]
)
DB_WRITE_ERRORS = Counter("logger_db_errors_total", "DB write errors")


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "10.10.10.101"),
        dbname=os.getenv("DB_NAME", "ml_predictions"),
        user=os.getenv("DB_USER", "ml_app"),
        password=os.getenv("DB_PASSWORD", "StrongPassword"),
        sslmode=os.getenv("DB_SSLMODE", "require"),
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "logger"})


@app.route("/log", methods=["POST"])
def log():
    data = request.get_json(force=True)
    input_data = data.get("input_data")
    prediction = data.get("prediction")
    model_version = data.get("model_version", "v1.0")

    if not input_data or not prediction:
        LOG_REQUESTS_TOTAL.labels(status="bad_request").inc()
        return jsonify({"error": "input_data and prediction required"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO predictions (input_data, prediction, model_version) "
            "VALUES (%s, %s, %s) RETURNING id",
            (json.dumps(input_data), json.dumps(prediction), model_version),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        LOG_REQUESTS_TOTAL.labels(status="success").inc()
        return jsonify({"status": "logged", "id": new_id}), 201
    except Exception as e:
        DB_WRITE_ERRORS.inc()
        LOG_REQUESTS_TOTAL.labels(status="error").inc()
        app.logger.error(f"DB error: {e}")
        return jsonify({"error": "db_error"}), 500


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
