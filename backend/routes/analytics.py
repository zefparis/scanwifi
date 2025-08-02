from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@bp.route('/dashboard', methods=['POST'])
def get_dashboard_metrics():
    """
    Compute and return dashboard metrics.
    Expects JSON with 'devices', 'access_points', and 'alerts'.
    """
    data = request.get_json()

    devices = data.get('devices', [])
    access_points = data.get('access_points', [])
    alerts = data.get('alerts', [])

    engine = current_app.analytics
    metrics = engine.compute_dashboard_metrics(devices, access_points, alerts)

    return jsonify(metrics)


@bp.route('/device', methods=['POST'])
def analyze_device():
    """
    Analyze a single device's behavior.
    Expects JSON with 'device', 'all_devices', and 'access_points'.
    """
    data = request.get_json()

    device = data.get('device')
    all_devices = data.get('all_devices', [])
    access_points = data.get('access_points', [])

    if not device:
        return jsonify({'status': 'error', 'message': 'Device data is required'}), 400

    engine = current_app.analytics
    analysis = engine.analyze_device_behavior(device, all_devices, access_points)

    return jsonify(analysis)
