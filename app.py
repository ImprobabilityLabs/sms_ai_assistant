from flask import Flask
from config import Config
from models import db 
from utils.logger import setup_logger
import routes.routes  

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)

    # Setup Logging
    logger = setup_logger('app_logger')
    app.logger.addHandler(logger)

    # Import routes to ensure they are registered with the app
    with app.app_context():
        import routes.routes

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
