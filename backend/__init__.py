from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    # Load environment variables
    load_dotenv()
    
    # Create and configure the app
    app = Flask(__name__)
    
    # Basic configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        MODE=os.getenv('MODE', 'mock'),
        KISMET_API_URL=os.getenv('KISMET_API_URL'),
        KISMET_API_KEY=os.getenv('KISMET_API_KEY'),
        DATA_FILE=os.getenv('DATA_FILE', 'mock_logs.json')
    )
    
    # Initialize components
    from . import loader, parser, analytics, alerts
    app.loader = loader.DataLoader(app)
    app.parser = parser.DataParser()
    app.analytics = analytics.AnalyticsEngine()
    app.alert_system = alerts.AlertSystem()
    
    # Register blueprints
    from .routes import dashboard, devices, accesspoints, alerts, logs
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(devices.bp)
    app.register_blueprint(accesspoints.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(logs.bp)
    
    return app
