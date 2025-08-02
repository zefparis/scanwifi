"""
BeNx - WiFi Analytics Dashboard Backend

Point d’entrée principal de l’API Flask.
Initialise l'application, les routes, les services de traitement et les erreurs.
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from datetime import datetime, timezone

# Chargement des variables d’environnement
load_dotenv()

def create_app():
    """Initialise et configure l’application Flask principale."""
    app = Flask(__name__)

    # Configuration de base
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
        DEBUG=os.environ.get('FLASK_ENV', 'development') == 'development',
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=True,
        MODE=os.environ.get('MODE', 'mock'),
        DATA_FILE=os.environ.get('DATA_FILE', 'data/mock_data.json'),
        KISMET_API_KEY=os.environ.get('KISMET_API_KEY', ''),
        KISMET_API_URL=os.environ.get('KISMET_API_URL', 'http://localhost:2501')
    )

    # 📦 Enregistrement des routes API
    from backend.routes import dashboard, devices, accesspoints, alerts, logs, analytics
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(devices.bp)
    app.register_blueprint(accesspoints.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(logs.bp)
    app.register_blueprint(analytics.bp)

    # ⚙️ Initialisation des services internes
    with app.app_context():
        from backend.loader import DataLoader
        from backend.parser import DataParser
        from backend.analytics import AnalyticsEngine
        from backend.alerts import AlertSystem

        app.loader = DataLoader(app)
        app.parser = DataParser(app)
        app.analytics = AnalyticsEngine(app)
        app.alert_system = AlertSystem(app)

        # Chargement initial des données
        try:
            data = app.loader.load_data()
            app.logger.info(f"[✓] Données chargées : {len(data.get('devices', []))} devices, "
                            f"{len(data.get('access_points', []))} points d’accès, "
                            f"{len(data.get('alerts', []))} alertes")
        except Exception as e:
            app.logger.error(f"[✗] Échec du chargement initial : {str(e)}")

    # 🔧 Gestion des erreurs
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'status': 'error',
            'message': 'La ressource demandée est introuvable.',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Une erreur interne est survenue.',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'status': 'error',
            'message': str(error.description) if hasattr(error, 'description') else 'Requête invalide',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 400

    # ✅ Endpoints de vérification
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'service': 'BeNx WiFi Analytics API',
            'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    # 🔗 Page d’accueil
    @app.route('/')
    def api_docs_redirect():
        return jsonify({
            'status': 'ok',
            'message': 'Bienvenue sur l’API BeNx WiFi Analytics',
            'documentation': 'https://github.com/yourusername/benx-api-docs',
            'endpoints': {
                'dashboard': '/api/dashboard',
                'devices': '/api/devices',
                'access_points': '/api/accesspoints',
                'alerts': '/api/alerts',
                'logs': '/api/logs',
                'analytics': '/api/analytics',
                'health': '/api/health'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    return app

# 🔥 Lancement de l’app si exécutée directement
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.debug)
