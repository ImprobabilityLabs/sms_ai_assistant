from flask import Flask
from config import Config
from models import db  # Assuming models/__init__.py initializes db
from utils.logger import setup_logger
from routes.route import route_blueprint  # Import the blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)

    # Setup Logging
    logger = setup_logger('app_logger')
    app.logger.addHandler(logger)
    
    # Register Blueprints
    app.register_blueprint(route_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
