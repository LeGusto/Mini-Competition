from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from routes.submission import submission_bp
from routes.general import general_bp
from routes.auth import auth_bp
from routes.contest import contest_bp
from services.connection import get_connection

app = Flask(__name__, static_folder="../frontend/build", static_url_path="")
CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.19.0.2:5173",
        "https://mini-competition-production.up.railway.app",
        "https://*.railway.app",
    ],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "Authorization"],
)

app.register_blueprint(submission_bp)
app.register_blueprint(general_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(contest_bp)


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    """Health check endpoint for Docker"""
    try:
        # Test database connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve frontend files"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
