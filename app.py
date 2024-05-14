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
    logger = setup_logger('app_logger',app.config['LOG_PATH'])
    app.logger.addHandler(logger)
    
    # Configure Routes
    configure_routes(app)

    # Create tables if they do not exist
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
