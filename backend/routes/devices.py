from flask import Blueprint, jsonify, request
from flask import current_app as app
from datetime import datetime, timezone, timedelta
import re

bp = Blueprint('devices', __name__, url_prefix='/api/devices')

@bp.route('', methods=['GET'])
def get_devices():
    """
    Get a list of all devices with optional filtering.
    Query parameters:
    - type: Filter by device type (e.g., smartphone, laptop)
    - min_signal: Minimum signal strength in dBm
    - max_signal: Maximum signal strength in dBm
    - zone: Filter by zone (e.g., lobby, cafe)
    - last_seen_minutes: Only include devices seen in the last X minutes
    - sort: Field to sort by (e.g., 'last_seen', 'signal_strength')
    - order: Sort order ('asc' or 'desc')
    """
    try:
        # Get query parameters
        device_type = request.args.get('type')
        min_signal = request.args.get('min_signal', type=int)
        max_signal = request.args.get('max_signal', type=int)
        zone = request.args.get('zone')
        last_seen_minutes = request.args.get('last_seen_minutes', type=int)
        sort_field = request.args.get('sort', 'last_seen')
        sort_order = request.args.get('order', 'desc')
        
        # Load device data
        data = app.loader.load_data()
        devices = data.get('devices', [])
        
        # Apply filters
        filtered_devices = []
        now = datetime.now(timezone.utc)
        
        for device in devices:
            # Skip if any filter doesn't match
            if device_type and device.get('device_type') != device_type:
                continue
                
            signal = device.get('signal_strength', -100)
            if min_signal is not None and signal < min_signal:
                continue
            if max_signal is not None and signal > max_signal:
                continue
                
            if zone and device.get('zone') != zone:
                continue
                
            # Filter by last seen time
            last_seen = device.get('last_seen')
            if last_seen_minutes and last_seen:
                if isinstance(last_seen, str):
                    try:
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        continue
                else:
                    last_seen_dt = last_seen
                    
                if (now - last_seen_dt) > timedelta(minutes=last_seen_minutes):
                    continue
            
            # Add device to filtered list
            filtered_devices.append(device)
        
        # Sort results
        if sort_field in ['last_seen', 'signal_strength', 'dwell_time_seconds']:
            reverse = sort_order.lower() == 'desc'
            filtered_devices.sort(
                key=lambda x: x.get(sort_field, 0) if x.get(sort_field) is not None else 0,
                reverse=reverse
            )
        
        # Prepare response
        response = {
            'status': 'success',
            'count': len(filtered_devices),
            'devices': filtered_devices,
            'timestamp': now.isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve device list',
            'error': str(e)
        }), 500

@bp.route('/<device_id>', methods=['GET'])
def get_device(device_id):
    """
    Get detailed information about a specific device.
    """
    try:
        # Load device data
        data = app.loader.load_data()
        
        # Find the device by ID (hashed MAC)
        device = next((d for d in data.get('devices', []) if d.get('mac') == device_id), None)
        
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Device not found'
            }), 404
        
        # Get analytics for this device
        analytics = app.analytics.analyze_device_behavior(
            device,
            data.get('devices', []),
            data.get('access_points', [])
        )
        
        # Prepare response
        response = {
            'status': 'success',
            'device': device,
            'analytics': analytics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_device: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve device details',
            'error': str(e)
        }), 500
