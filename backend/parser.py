from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import re

class DataParser:
    """
    Parse et nettoie les données brutes WiFi (appareils, points d'accès, alertes).
    """

    def __init__(self, app):
        self.app = app
        self.mac_regex = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')

    def parse_device(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        try:
            first_seen = self._parse_timestamp(raw.get("first_seen"))
            last_seen = self._parse_timestamp(raw.get("last_seen"))

            return {
                "mac": self._normalize_mac(raw.get("mac", "")),
                "signal": self._normalize_signal(raw.get("signal_strength")),
                "ssids": self._clean_ssid_list(raw.get("ssids", [])),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "dwell_time_seconds": self._calculate_dwell_time(first_seen, last_seen),
                "device_type": self._normalize_device_type(raw.get("device_type")),
                "zone": self._normalize_zone(raw.get("zone")),
            }
        except Exception as e:
            self.app.logger.error(f"[DataParser] Failed to parse device: {e}")
            return {}

    def parse_access_point(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "bssid": self._normalize_mac(raw.get("bssid", "")),
                "ssid": self._clean_ssid(raw.get("ssid", "")),
                "encryption": self._normalize_encryption(raw.get("encryption")),
                "channel": self._normalize_channel(raw.get("channel")),
                "signal_strength": self._normalize_signal(raw.get("signal_strength")),
            }
        except Exception as e:
            self.app.logger.error(f"[DataParser] Failed to parse access point: {e}")
            return {}

    def parse_alert(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "id": str(raw.get("id", "")),
                "type": self._normalize_alert_type(raw.get("type")),
                "severity": self._normalize_severity(raw.get("severity")),
                "message": str(raw.get("message", "")).strip(),
                "timestamp": self._parse_timestamp(raw.get("timestamp")),
            }
        except Exception as e:
            self.app.logger.error(f"[DataParser] Failed to parse alert: {e}")
            return {}

    # ---------- Helpers ----------

    def _normalize_mac(self, mac: str) -> str:
        if not mac:
            return ''
        cleaned = ''.join(c.lower() for c in mac if c.isalnum())
        return ':'.join(cleaned[i:i + 2] for i in range(0, 12, 2)) if len(cleaned) == 12 else ''

    def _normalize_signal(self, rssi: Any) -> int:
        try:
            val = int(rssi)
            return max(-120, min(0, val))
        except:
            return -100

    def _clean_ssid(self, ssid: str) -> str:
        if not ssid or not isinstance(ssid, str):
            return ''
        cleaned = ''.join(c for c in ssid if 32 <= ord(c) <= 126)
        return cleaned.encode('utf-8')[:32].decode('utf-8', 'ignore')

    def _clean_ssid_list(self, ssids: List[str]) -> List[str]:
        seen, result = set(), []
        for ssid in ssids:
            clean = self._clean_ssid(ssid)
            if clean and clean not in seen:
                seen.add(clean)
                result.append(clean)
        return result

    def _parse_timestamp(self, ts: Any) -> Optional[datetime]:
        if not ts:
            return None
        try:
            if isinstance(ts, (int, float)):
                ts = ts / 1000 if ts > 1e10 else ts
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        except:
            return None

    def _calculate_dwell_time(self, first: Optional[datetime], last: Optional[datetime]) -> int:
        if first and last:
            try:
                return max(0, int((last - first).total_seconds()))
            except:
                return 0
        return 0

    def _normalize_device_type(self, t: Any) -> str:
        mapping = {
            'phone': 'smartphone', 'tablet': 'tablet',
            'laptop': 'laptop', 'desktop': 'computer',
            'computer': 'computer', 'iot': 'iot',
            'printer': 'printer', 'tv': 'smart_tv',
            'smart-tv': 'smart_tv', 'watch': 'smart_watch',
        }
        key = str(t).lower().strip()
        return mapping.get(key, 'unknown')

    def _normalize_zone(self, z: Any) -> str:
        zones = {'entry', 'exit', 'lobby', 'shop', 'cafe', 'office', 'meeting', 'conference', 'unknown'}
        name = str(z).lower().strip()
        return name if name in zones else 'unknown'

    def _normalize_encryption(self, e: Any) -> str:
        valid = {'NONE', 'WEP', 'WPA', 'WPA2', 'WPA3', 'WPA2-ENTERPRISE', 'WPA3-ENTERPRISE', 'UNKNOWN', 'OPEN'}
        val = str(e).upper().strip()
        return val if val in valid else 'UNKNOWN'

    def _normalize_channel(self, c: Any) -> int:
        try:
            ch = int(c)
            return max(1, min(165, ch))
        except:
            return 1

    def _normalize_alert_type(self, t: Any) -> str:
        known = {'rogue_ap', 'rogue_dhcp', 'deauth_attack', 'evil_twin', 'karma_attack', 'mac_spoofing',
                 'channel_hopping', 'weak_encryption', 'unknown', 'security_alert'}
        key = str(t).lower().replace(' ', '_')
        return key if key in known else 'unknown'

    def _normalize_severity(self, s: Any) -> str:
        levels = {'low', 'medium', 'high', 'critical'}
        level = str(s).lower()
        return level if level in levels else 'medium'
