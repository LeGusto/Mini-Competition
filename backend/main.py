from flask import Flask
from flask_cors import CORS
from routes.submission import submission_bp
from routes.general import general_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(submission_bp)
app.register_blueprint(general_bp)

if __name__ == "__main__":
    app.run(debug=True)
