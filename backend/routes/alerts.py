from flask import Blueprint, jsonify, request
from flask import current_app as app
from datetime import datetime, timezone, timedelta

bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@bp.route('', methods=['GET'])
def get_alerts():
    """
    Get a list of all alerts with optional filtering.
    Query parameters:
    - severity: Filter by severity level (e.g., 'high', 'medium', 'low')
    - type: Filter by alert type (e.g., 'rogue_ap', 'mac_spoofing')
    - acknowledged: Filter by acknowledged status (true/false)
    - start_time: Only include alerts after this ISO timestamp
    - end_time: Only include alerts before this ISO timestamp
    - limit: Maximum number of alerts to return (default: 100)
    """
    try:
        # Get query parameters
        severity_filter = request.args.get('severity')
        type_filter = request.args.get('type')
        acknowledged_filter = request.args.get('acknowledged')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        limit = min(int(request.args.get('limit', 100)), 1000)  # Cap at 1000
        
        # Parse timestamp filters
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid start_time format. Use ISO 8601 format.'
                }), 400
        
        end_time = None
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid end_time format. Use ISO 8601 format.'
                }), 400
        
        # Parse acknowledged filter
        acknowledged = None
        if acknowledged_filter is not None:
            acknowledged = acknowledged_filter.lower() == 'true'
        
        # Get alerts from the alert system
        alerts = app.alert_system.analyze_devices(
            app.loader.load_data().get('devices', []),
            app.loader.load_data().get('access_points', [])
        )
        
        # Apply filters
        filtered_alerts = []
        
        for alert in alerts:
            # Skip if any filter doesn't match
            if severity_filter and alert.get('severity') != severity_filter.lower():
                continue
                
            if type_filter and alert.get('type') != type_filter.lower():
                continue
                
            if acknowledged is not None and alert.get('acknowledged') != acknowledged:
                continue
            
            # Filter by timestamp
            alert_time = datetime.fromisoformat(alert.get('timestamp').replace('Z', '+00:00'))
            if start_time and alert_time < start_time:
                continue
            if end_time and alert_time > end_time:
                continue
            
            # Add alert to filtered list
            filtered_alerts.append(alert)
            
            # Apply limit
            if len(filtered_alerts) >= limit:
                break
        
        # Sort by timestamp (newest first)
        filtered_alerts.sort(
            key=lambda x: datetime.fromisoformat(x.get('timestamp').replace('Z', '+00:00')),
            reverse=True
        )
        
        # Prepare response
        response = {
            'status': 'success',
            'count': len(filtered_alerts),
            'alerts': filtered_alerts,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_alerts: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve alerts',
            'error': str(e)
        }), 500

@bp.route('/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Acknowledge an alert to mark it as reviewed.
    """
    try:
        # Find the alert in active alerts
        alert = app.alert_system.active_alerts.get(alert_id)
        
        if not alert:
            return jsonify({
                'status': 'error',
                'message': 'Alert not found or already acknowledged'
            }), 404
        
        # Mark as acknowledged
        alert.acknowledged = True
        app.alert_system.acknowledged_alerts.add(alert_id)
        
        # Prepare response
        response = {
            'status': 'success',
            'message': f'Alert {alert_id} acknowledged',
            'alert': alert.to_dict(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in acknowledge_alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to acknowledge alert',
            'error': str(e)
        }), 500
