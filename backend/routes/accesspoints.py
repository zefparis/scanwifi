from flask import Blueprint, jsonify, request
from flask import current_app as app
from datetime import datetime, timezone, timedelta

bp = Blueprint('accesspoints', __name__, url_prefix='/api/accesspoints')

@bp.route('', methods=['GET'])
def get_access_points():
    """
    Get a list of all access points with optional filtering.
    Query parameters:
    - ssid: Filter by SSID (case-insensitive partial match)
    - encryption: Filter by encryption type (e.g., 'WPA2', 'WPA3', 'NONE')
    - min_channel: Minimum channel number
    - max_channel: Maximum channel number
    - min_signal: Minimum signal strength in dBm
    - max_signal: Maximum signal strength in dBm
    - sort: Field to sort by (e.g., 'ssid', 'signal_strength', 'channel')
    - order: Sort order ('asc' or 'desc')
    """
    try:
        # Get query parameters
        ssid_filter = request.args.get('ssid', '').lower()
        encryption_filter = request.args.get('encryption')
        min_channel = request.args.get('min_channel', type=int)
        max_channel = request.args.get('max_channel', type=int)
        min_signal = request.args.get('min_signal', type=int)
        max_signal = request.args.get('max_signal', type=int)
        sort_field = request.args.get('sort', 'ssid')
        sort_order = request.args.get('order', 'asc')
        
        # Load access point data
        data = app.loader.load_data()
        access_points = data.get('access_points', [])
        
        # Apply filters
        filtered_aps = []
        
        for ap in access_points:
            # Skip if any filter doesn't match
            ssid = ap.get('ssid', '').lower()
            if ssid_filter and ssid_filter not in ssid:
                continue
                
            if encryption_filter and ap.get('encryption', '').upper() != encryption_filter.upper():
                continue
                
            channel = ap.get('channel', 0)
            if min_channel is not None and channel < min_channel:
                continue
            if max_channel is not None and channel > max_channel:
                continue
                
            signal = ap.get('signal_strength', -100)
            if min_signal is not None and signal < min_signal:
                continue
            if max_signal is not None and signal > max_signal:
                continue
            
            # Add AP to filtered list
            filtered_aps.append(ap)
        
        # Sort results
        if sort_field in ['ssid', 'channel', 'signal_strength']:
            reverse = sort_order.lower() == 'desc'
            filtered_aps.sort(
                key=lambda x: (
                    x.get(sort_field, '').lower() 
                    if isinstance(x.get(sort_field), str) 
                    else x.get(sort_field, 0)
                ),
                reverse=reverse
            )
        
        # Prepare response
        response = {
            'status': 'success',
            'count': len(filtered_aps),
            'access_points': filtered_aps,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_access_points: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve access points',
            'error': str(e)
        }), 500

@bp.route('/<ap_id>', methods=['GET'])
def get_access_point(ap_id):
    """
    Get detailed information about a specific access point.
    """
    try:
        # Load access point data
        data = app.loader.load_data()
        
        # Find the AP by BSSID or SSID
        ap = next((ap for ap in data.get('access_points', []) 
                  if ap.get('bssid') == ap_id or ap.get('ssid') == ap_id), None)
        
        if not ap:
            return jsonify({
                'status': 'error',
                'message': 'Access point not found'
            }), 404
        
        # Find connected devices
        connected_devices = [
            device for device in data.get('devices', [])
            if ap.get('ssid') in device.get('ssids', []) or 
               ap.get('bssid') in device.get('bssids', [])
        ]
        
        # Prepare response
        response = {
            'status': 'success',
            'access_point': ap,
            'connected_devices_count': len(connected_devices),
            'connected_devices': [{
                'mac': d.get('mac'),
                'device_type': d.get('device_type'),
                'signal_strength': d.get('signal_strength')
            } for d in connected_devices[:10]],  # Limit to first 10 devices
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_access_point: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve access point details',
            'error': str(e)
        }), 500
