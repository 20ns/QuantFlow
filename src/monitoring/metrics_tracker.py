"""
Real-time metrics tracker for performance and risk
"""
from typing import Dict, Any
from datetime import datetime

class MetricsTracker:
    def __init__(self):
        self.metrics = {}

    def update(self, key: str, value: Any):
        self.metrics[key] = value
        self.metrics['last_update'] = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
