from flask import Flask
from flask_cors import CORS
from routes.submission import submission_bp
from routes.general import general_bp
from routes.auth import auth_bp
from routes.contest import contest_bp

app = Flask(__name__)
CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.19.0.2:5173",
    ],
    supports_credentials=True,
)

app.register_blueprint(submission_bp)
app.register_blueprint(general_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(contest_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
