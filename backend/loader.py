import json
import os
import requests
from datetime import datetime
from .utils.hashmac import hash_mac_address

class DataLoader:
    def __init__(self, app):
        self.app = app
        self.data = {
            'devices': [],
            'access_points': [],
            'alerts': []
        }
        self.last_updated = None
        
    def load_data(self):
        """Load data based on the current mode (mock or live)."""
        if self.app.config['MODE'] == 'mock':
            self._load_mock_data()
        else:
            self._load_live_data()
        self.last_updated = datetime.utcnow()
        return self.data
    
    def _load_mock_data(self):
        """Load data from the mock JSON file."""
        try:
            data_file = os.path.join(os.path.dirname(__file__), '..', self.app.config['DATA_FILE'])
            with open(data_file, 'r') as f:
                raw_data = json.load(f)
                self._process_raw_data(raw_data)
        except Exception as e:
            self.app.logger.error(f"Error loading mock data: {str(e)}")
            raise
    
    def _load_live_data(self):
        """Load data from the Kismet API."""
        try:
            headers = {
                'Kismet': f"sessionid={self.app.config['KISMET_API_KEY']}",
                'Accept': 'application/json'
            }
            
            # Fetch devices
            devices_url = f"{self.app.config['KISMET_API_URL']}/devices/views/all/devices.json"
            response = requests.get(devices_url, headers=headers)
            response.raise_for_status()
            raw_devices = response.json()
            
            # Fetch alerts
            alerts_url = f"{self.app.config['KISMET_API_URL']}/alerts/definitions.json"
            response = requests.get(alerts_url, headers=headers)
            raw_alerts = response.json() if response.status_code == 200 else []
            
            self._process_raw_data({
                'devices': raw_devices,
                'alerts': raw_alerts
            })
            
        except Exception as e:
            self.app.logger.error(f"Error loading live data: {str(e)}")
            raise
    
    def _process_raw_data(self, raw_data):
        """Process and normalize raw data from either source."""
        # Process devices
        self.data['devices'] = [
            self._process_device(device) 
            for device in raw_data.get('devices', [])
        ]
        
        # Process access points
        self.data['access_points'] = [
            self._process_access_point(ap)
            for ap in raw_data.get('access_points', [])
        ]
        
        # Process alerts
        self.data['alerts'] = raw_data.get('alerts', [])
    
    def _process_device(self, device):
        """Process a single device entry."""
        # Hash the MAC address for privacy
        hashed_mac = hash_mac_address(device.get('mac', ''))
        
        return {
            'id': hashed_mac,
            'mac': hashed_mac,  # Store only the hashed version
            'signal_strength': device.get('signal_strength', -100),
            'ssids': device.get('ssids', []),
            'first_seen': device.get('first_seen'),
            'last_seen': device.get('last_seen'),
            'device_type': device.get('device_type', 'unknown'),
            'zone': device.get('zone', 'unknown')
        }
    
    def _process_access_point(self, ap):
        """Process a single access point entry."""
        return {
            'bssid': ap.get('bssid'),
            'ssid': ap.get('ssid', 'hidden'),
            'encryption': ap.get('encryption', 'unknown'),
            'channel': ap.get('channel', 0),
            'signal_strength': ap.get('signal_strength', -100)
        }
    
    def get_summary_stats(self):
        """Get summary statistics about the loaded data."""
        if not self.data['devices']:
            self.load_data()
            
        return {
            'total_devices': len(self.data['devices']),
            'total_aps': len(self.data['access_points']),
            'active_alerts': len(self.data['alerts']),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
