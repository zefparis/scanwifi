from flask import Blueprint, jsonify
from flask import current_app as app
from datetime import datetime, timezone

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics including device counts, signal strength, and alerts.
    """
    try:
        # Get data from the data loader
        data = app.loader.load_data()
        
        # Get analytics
        stats = app.analytics.compute_dashboard_metrics(
            data.get('devices', []),
            data.get('access_points', []),
            data.get('alerts', [])
        )
        
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_dashboard_stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve dashboard statistics',
            'error': str(e)
        }), 500
