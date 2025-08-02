from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import re

@dataclass
class Alert:
    """Represents a security or operational alert."""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    source: str = ""
    details: Dict[str, Any] = None
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.alert_id,
            'type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'details': self.details or {},
            'acknowledged': self.acknowledged
        }

class AlertSystem:
    """Manages security and operational alerts for the WiFi analytics system."""
    
    def __init__(self, app):
        self.app = app
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.acknowledged_alerts: Set[str] = set()
        self.alert_rules = self._initialize_alert_rules()

    
    def _initialize_alert_rules(self) -> Dict[str, Dict]:
        return {
            'rogue_ap': {
                'enabled': True,
                'severity': 'high',
                'message': 'Rogue access point detected: {ssid} ({bssid})',
                'suppress_after': 24,
                'thresholds': {'signal_strength': -70, 'encryption': ['NONE', 'WEP']}
            },
            'mac_spoofing': {
                'enabled': True,
                'severity': 'high',
                'message': 'Possible MAC address spoofing detected for vendor {vendor}',
                'suppress_after': 1,
                'thresholds': {'same_vendor_macs': 3}
            },
            'weak_encryption': {
                'enabled': True,
                'severity': 'medium',
                'message': 'Weak encryption detected: {ssid} uses {encryption}',
                'suppress_after': 24,
                'thresholds': {'weak_encryption_types': ['WEP', 'WPA']}
            }
        }
    
    def analyze_devices(self, devices: List[Dict], access_points: List[Dict]) -> List[Dict]:
        """Analyze devices and access points for potential security issues."""
        new_alerts = []
        
        # Check for rogue APs and weak encryption
        ap_ssids = {}
        for ap in access_points:
            ssid = ap.get('ssid')
            bssid = ap.get('bssid')
            if not ssid or not bssid:
                continue
                
            # Check for duplicate SSIDs (possible rogue AP)
            if ssid in ap_ssids and bssid != ap_ssids[ssid]:
                new_alerts.append(self._create_alert(
                    'rogue_ap', 
                    f"rogue_ap_{bssid}",
                    bssid,
                    {'ssid': ssid, 'bssid': bssid}
                ))
            else:
                ap_ssids[ssid] = bssid
            
            # Check for weak encryption
            encryption = ap.get('encryption', '').upper()
            if encryption in self.alert_rules['weak_encryption']['thresholds']['weak_encryption_types']:
                new_alerts.append(self._create_alert(
                    'weak_encryption',
                    f"weak_enc_{bssid}",
                    bssid,
                    {'ssid': ssid, 'bssid': bssid, 'encryption': encryption}
                ))
        
        # Check for MAC spoofing
        oui_devices = {}
        for device in devices:
            mac = device.get('mac', '').upper()
            if not mac or ':' not in mac:
                continue
                
            oui = ':'.join(mac.split(':')[:3])
            if oui not in oui_devices:
                oui_devices[oui] = set()
            oui_devices[oui].add(mac)
        
        # Check for potential MAC spoofing
        for oui, macs in oui_devices.items():
            if len(macs) >= self.alert_rules['mac_spoofing']['thresholds']['same_vendor_macs']:
                vendor = self._get_vendor_name(oui) or f"OUI {oui}"
                new_alerts.append(self._create_alert(
                    'mac_spoofing',
                    f"mac_spoofing_{oui}",
                    oui,
                    {
                        'vendor': vendor,
                        'oui': oui,
                        'device_count': len(macs),
                        'mac_addresses': list(macs)[:5]  # Limit to first 5 MACs
                    }
                ))
        
        # Add new alerts to the system
        for alert in new_alerts:
            self._add_alert(alert)
        
        # Clean up old alerts
        self._cleanup_old_alerts()
        
        return [a.to_dict() for a in new_alerts]
    
    def _create_alert(self, alert_type: str, alert_id: str, source: str, details: Dict) -> Alert:
        """Helper to create a new alert."""
        rule = self.alert_rules.get(alert_type, {})
        message = rule.get('message', 'Security alert detected').format(**details)
        
        return Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=rule.get('severity', 'medium'),
            message=message,
            timestamp=datetime.now(timezone.utc),
            source=source,
            details=details
        )
    
    def _add_alert(self, alert: Alert) -> None:
        """Add an alert to the system if it doesn't already exist."""
        if alert.alert_id not in self.active_alerts:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            self.app.logger.info(f"[ALERT] {alert.alert_type} - {alert.message}")
    
    def _cleanup_old_alerts(self) -> None:
        """Remove old alerts from the active alerts."""
        now = datetime.now(timezone.utc)
        expired_alerts = []
        
        for alert_id, alert in list(self.active_alerts.items()):
            rule = self.alert_rules.get(alert.alert_type, {})
            suppress_hours = rule.get('suppress_after', 24)
            
            if (now - alert.timestamp) > timedelta(hours=suppress_hours):
                expired_alerts.append(alert_id)
        
        for alert_id in expired_alerts:
            self.active_alerts.pop(alert_id, None)
    
    def _get_vendor_name(self, oui: str) -> str:
        """Get vendor name from OUI (simplified version)."""
        oui_map = {
            '00:1A:2B': 'Cisco',
            '00:0C:29': 'VMware',
            '00:50:56': 'VMware',
            '00:1C:42': 'Parallels',
            '08:00:27': 'Oracle VirtualBox',
            '08:00:0B': 'Intel',
            '00:1B:63': 'Apple',
            '00:03:93': 'Apple',
            '00:0A:27': 'Apple',
            '00:1D:4F': 'Apple',
            '00:1E:52': 'Apple'
        }
        return oui_map.get(oui.upper(), '')
