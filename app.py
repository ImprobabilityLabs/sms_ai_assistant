from flask import Flask
from config import DevelopmentConfig
from models import db  # Assuming models/__init__.py initializes db
from utils.logger import setup_logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # Initialize Extensions
    db.init_app(app)
    setup_logging()

    # Import routes to register them
    import routes.route

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
