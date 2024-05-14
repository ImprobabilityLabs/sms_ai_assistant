from flask import Flask
from config import Config
from models import db 
from utils.logger import setup_logger
from routes.routes import configure_routes  

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)

    # Setup Logging
    logger = setup_logger('app_logger')
    app.logger.addHandler(logger)

    # Configure Routes
    configure_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
