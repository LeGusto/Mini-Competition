from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from services.connection import get_connection
from routes.submission import submission_bp
from routes.general import general_bp
from routes.auth import auth_bp
from routes.contest import contest_bp

app = Flask(__name__, static_folder="static", static_url_path="/static")
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

# Register blueprints
app.register_blueprint(submission_bp)
app.register_blueprint(general_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(contest_bp)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path=""):
    """Serve frontend files for all non-API routes"""
    print(f"Serving frontend for path: '{path}'")

    # Skip API routes - they should be handled by blueprints
    # But if we get here, it means the API route wasn't found
    if path and any(
        path.startswith(prefix)
        for prefix in ["api/", "auth/", "submission/", "general/"]
    ):
        print(f"API route not found: {path}")
        return jsonify({"error": "API endpoint not found", "path": path}), 404

    # Special handling for contest routes - don't treat them as API routes
    # when they're being accessed from the frontend SPA

    try:
        # Check if it's a static file request (has file extension)
        if path and "." in path:
            file_path = os.path.join(app.static_folder, path)
            print(f"Checking static file: {file_path}")

            if os.path.exists(file_path) and os.path.isfile(file_path):
                print(f"Serving static file: {path}")

                # Serve the file with proper MIME type
                response = send_from_directory(app.static_folder, path)

                # Set proper MIME types based on file extension
                if path.endswith(".js"):
                    response.headers["Content-Type"] = (
                        "application/javascript; charset=utf-8"
                    )
                elif path.endswith(".css"):
                    response.headers["Content-Type"] = "text/css; charset=utf-8"
                elif path.endswith(".html"):
                    response.headers["Content-Type"] = "text/html; charset=utf-8"
                elif path.endswith(".json"):
                    response.headers["Content-Type"] = "application/json; charset=utf-8"

                return response

        # For SPA routes (no extension or doesn't exist as file), serve index.html
        index_path = os.path.join(app.static_folder, "index.html")
        print(f"Checking index.html at: {index_path}")

        if os.path.exists(index_path):
            print(f"Serving index.html for SPA route: {path}")
            response = send_from_directory(app.static_folder, "index.html")
            response.headers["Content-Type"] = "text/html; charset=utf-8"
            return response
        else:
            print("index.html not found!")
            return jsonify(
                {
                    "message": "Mini-Competition API is working!",
                    "status": "success",
                    "note": "Frontend files not found, but API is ready",
                    "static_folder": app.static_folder,
                    "path": path,
                }
            )
    except Exception as e:
        print(f"Exception in serve_frontend: {e}")
        return jsonify(
            {
                "message": "Mini-Competition API is working!",
                "status": "success",
                "error": str(e),
                "path": path,
            }
        )


@app.route("/test", methods=["GET"])
def test():
    """Test endpoint"""
    return jsonify({"message": "Test endpoint working!", "status": "success"})


@app.route("/debug-routes")
def debug_routes():
    """Debug endpoint to show all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(
            {
                "rule": str(rule),
                "methods": list(rule.methods),
                "endpoint": rule.endpoint,
            }
        )
    return jsonify({"routes": routes})


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
