from flask import Blueprint, jsonify, request
from flask import current_app as app
from datetime import datetime, timezone, timedelta
import json

bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@bp.route('', methods=['GET'])
def get_logs():
    """
    Get recent log entries with optional filtering.
    Query parameters:
    - level: Filter by log level (e.g., 'info', 'warning', 'error')
    - source: Filter by log source (e.g., 'system', 'security')
    - start_time: Only include logs after this ISO timestamp
    - end_time: Only include logs before this ISO timestamp
    - limit: Maximum number of log entries to return (default: 100, max: 1000)
    - search: Text to search in log messages (case-insensitive)
    """
    try:
        # Get query parameters
        level_filter = request.args.get('level')
        source_filter = request.args.get('source')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        search_text = request.args.get('search', '').lower()
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
        
        # In a production system, this would query a proper logging database
        # For this example, we'll simulate log entries based on recent activity
        simulated_logs = []
        now = datetime.now(timezone.utc)
        
        # Simulate some recent log entries
        simulated_logs.extend([
            {
                'timestamp': (now - timedelta(minutes=i)).isoformat(),
                'level': 'info',
                'source': 'system',
                'message': f'System check completed successfully',
                'details': {}
            } for i in range(0, 10, 2)  # Every 2 minutes for the last 20 minutes
        ])
        
        # Add some security-related logs
        simulated_logs.extend([
            {
                'timestamp': (now - timedelta(minutes=i)).isoformat(),
                'level': 'warning',
                'source': 'security',
                'message': f'Failed login attempt from 192.168.1.{i}',
                'details': {'ip': f'192.168.1.{i}', 'attempts': 1}
            } for i in range(1, 5)  # 4 failed attempts
        ])
        
        # Add some error logs
        if now.minute % 5 == 0:  # Every 5 minutes
            simulated_logs.append({
                'timestamp': now.isoformat(),
                'level': 'error',
                'source': 'api',
                'message': 'Failed to process API request',
                'details': {'endpoint': '/api/devices', 'status_code': 500}
            })
        
        # Apply filters
        filtered_logs = []
        
        for log in simulated_logs:
            # Skip if any filter doesn't match
            if level_filter and log.get('level') != level_filter.lower():
                continue
                
            if source_filter and log.get('source') != source_filter.lower():
                continue
            
            # Filter by timestamp
            log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            if start_time and log_time < start_time:
                continue
            if end_time and log_time > end_time:
                continue
            
            # Search in message
            if search_text and search_text not in log.get('message', '').lower():
                continue
            
            # Add log to filtered list
            filtered_logs.append(log)
            
            # Apply limit
            if len(filtered_logs) >= limit:
                break
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(
            key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')),
            reverse=True
        )
        
        # Prepare response
        response = {
            'status': 'success',
            'count': len(filtered_logs),
            'logs': filtered_logs,
            'timestamp': now.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve logs',
            'error': str(e)
        }), 500
