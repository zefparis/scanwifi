from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import statistics

class AnalyticsEngine:
    """
    Moteur d’analyse pour les données WiFi.
    Traite les devices, alertes, signaux, comportements et anomalies.
    """
    def __init__(self, app):
        self.app = app  # Référence à l'application Flask
        self.device_history = defaultdict(list)

        self.anomaly_thresholds = {
            'signal_jump': 20,  # Variation brutale de signal
            'rapid_movement': 3,  # Changements de zone rapides
            'unusual_hour': {
                'weekday': (0, 5),  # 00h-5h la semaine
                'weekend': (0, 7)   # 00h-7h le week-end
            }
        }

    def compute_dashboard_metrics(self, devices: List[Dict], access_points: List[Dict], alerts: List[Dict]) -> Dict[str, Any]:
        """Retourne les métriques globales du dashboard."""
        now = datetime.now(timezone.utc)
        signal_strengths = [d.get('signal_strength', -100) for d in devices]
        dwell_times = [d.get('dwell_time_seconds', 0) / 60 for d in devices]

        return {
            'summary': {
                'total_devices': len(devices),
                'recent_devices': sum(1 for d in devices if self._is_recent(d.get('last_seen'), minutes=15)),
                'total_aps': len(access_points),
                'active_alerts': len(alerts),
                'avg_signal_strength': round(statistics.mean(signal_strengths), 1) if signal_strengths else -100,
                'avg_dwell_time_minutes': round(statistics.mean(dwell_times), 1) if dwell_times else 0
            },
            'device_types': self._count_device_types(devices),
            'ssid_popularity': self._count_ssid_popularity(devices, access_points),
            'zone_distribution': self._compute_zone_distribution(devices),
            'encryption_stats': self._compute_encryption_stats(access_points),
            'channel_utilization': self._compute_channel_utilization(access_points),
            'timestamp': now.isoformat()
        }

    def _is_recent(self, timestamp: Optional[datetime], minutes: int = 15) -> bool:
        """Vérifie si l’activité est récente."""
        if not timestamp:
            return False
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except Exception:
                return False
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - timestamp) <= timedelta(minutes=minutes)

    def _count_device_types(self, devices: List[Dict]) -> Dict[str, int]:
        return Counter(d.get('device_type', 'unknown') for d in devices)

    def _count_ssid_popularity(self, devices: List[Dict], access_points: List[Dict]) -> List[Dict]:
        ssid_counter = Counter()
        for d in devices:
            ssid_counter.update(d.get('ssids', []))
        for ap in access_points:
            ssid = ap.get('ssid')
            if ssid and ssid not in ssid_counter:
                ssid_counter[ssid] = 0
        return sorted(
            [{'ssid': ssid, 'count': count} for ssid, count in ssid_counter.items()],
            key=lambda x: x['count'],
            reverse=True
        )

    def _compute_zone_distribution(self, devices: List[Dict]) -> Dict[str, int]:
        return dict(Counter(d.get('zone', 'unknown') for d in devices))

    def _compute_encryption_stats(self, access_points: List[Dict]) -> Dict[str, int]:
        return dict(Counter(ap.get('encryption', 'unknown').upper() for ap in access_points))

    def _compute_channel_utilization(self, access_points: List[Dict]) -> Dict[int, int]:
        return dict(Counter(ap.get('channel', 0) for ap in access_points))
