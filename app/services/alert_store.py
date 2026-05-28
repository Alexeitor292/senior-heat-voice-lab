from typing import Any
from uuid import uuid4


class AlertStore:
    def __init__(self):
        self._alerts: dict[str, dict[str, Any]] = {}

    def create_alert(self, payload: dict[str, Any]) -> str:
        alert_id = str(uuid4())
        self._alerts[alert_id] = payload
        return alert_id

    def get_alert(self, alert_id: str) -> dict[str, Any] | None:
        return self._alerts.get(alert_id)


alert_store = AlertStore()