from flask import Flask, render_template
from config import Config
from database.mongodb import init_db

# Import modular blueprints
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.iq import iq_bp
from routes.report import report_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize MongoDB Connection
    try:
        init_db(app)
    except Exception as e:
        print(f"[Warning] MongoDB Initialization Error: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(iq_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)