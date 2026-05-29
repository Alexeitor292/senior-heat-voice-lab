import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import (
    HeatRiskObservation,
    HeatTriggeredCall,
    SeniorHeatSettings,
)
from app.services.profile_service import profile_service
from app.services.twilio_service import twilio_service


NWS_HEATRISK_IMAGE_SERVER = (
    "https://mapservices.weather.noaa.gov/experimental/rest/services/"
    "NWS_HeatRisk/ImageServer"
)


HEAT_RISK_LABELS = {
    0: "Little to no risk",
    1: "Minor",
    2: "Moderate",
    3: "Major",
    4: "Extreme",
}


def heat_risk_label(value: int) -> str:
    return HEAT_RISK_LABELS.get(value, "Unknown")


def _settings_to_dict(row: SeniorHeatSettings) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "enabled": row.enabled,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "city": row.city,
        "state": row.state,
        "zip_code": row.zip_code,
        "timezone": row.timezone,
        "trigger_threshold": row.trigger_threshold,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _observation_to_dict(row: HeatRiskObservation) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "provider": row.provider,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "heat_risk_value": row.heat_risk_value,
        "heat_risk_label": row.heat_risk_label,
        "source_url": row.source_url,
        "observed_at": row.observed_at.isoformat() if row.observed_at else None,
    }


def _triggered_call_to_dict(row: HeatTriggeredCall) -> dict[str, Any]:
    return {
        "id": row.id,
        "senior_id": row.senior_id,
        "local_date": row.local_date,
        "heat_risk_value": row.heat_risk_value,
        "heat_risk_label": row.heat_risk_label,
        "started": row.started,
        "senior_call_sid": row.senior_call_sid,
        "reason": row.reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _coerce_heat_risk_value(value: Any) -> int:
    """
    NWS raster values may come back as int, float, or string.
    Clamp to the HeatRisk 0-4 range.
    """

    numeric = int(round(float(value)))

    if numeric < 0:
        return 0

    if numeric > 4:
        return 4

    return numeric


class HeatRiskService:
    def upsert_heat_settings(
        self,
        senior_id: int,
        enabled: bool,
        latitude: float | None,
        longitude: float | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
        timezone_name: str,
        trigger_threshold: int,
    ) -> dict[str, Any] | None:
        senior = profile_service.get_senior(senior_id)

        if not senior:
            return None

        if trigger_threshold < 0 or trigger_threshold > 4:
            raise ValueError("trigger_threshold must be between 0 and 4.")

        if latitude is not None and (latitude < -90 or latitude > 90):
            raise ValueError("latitude must be between -90 and 90.")

        if longitude is not None and (longitude < -180 or longitude > 180):
            raise ValueError("longitude must be between -180 and 180.")

        # Validate timezone.
        ZoneInfo(timezone_name)

        with SessionLocal() as db:
            row = (
                db.query(SeniorHeatSettings)
                .filter(SeniorHeatSettings.senior_id == senior_id)
                .first()
            )

            if not row:
                row = SeniorHeatSettings(senior_id=senior_id)
                db.add(row)

            row.enabled = enabled
            row.latitude = latitude
            row.longitude = longitude
            row.city = city
            row.state = state
            row.zip_code = zip_code
            row.timezone = timezone_name
            row.trigger_threshold = trigger_threshold

            db.commit()
            db.refresh(row)

            return _settings_to_dict(row)

    def get_heat_settings(
        self,
        senior_id: int,
    ) -> dict[str, Any] | None:
        with SessionLocal() as db:
            row = (
                db.query(SeniorHeatSettings)
                .filter(SeniorHeatSettings.senior_id == senior_id)
                .first()
            )

            if not row:
                return None

            return _settings_to_dict(row)

    def list_heat_settings(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(SeniorHeatSettings)
                .order_by(SeniorHeatSettings.created_at.desc())
                .all()
            )

            return [_settings_to_dict(row) for row in rows]

    def get_current_heat_risk_for_senior(
        self,
        senior_id: int,
    ) -> dict[str, Any]:
        heat_settings = self.get_heat_settings(senior_id)

        if not heat_settings:
            raise ValueError("Senior heat settings not found.")

        if not heat_settings["enabled"]:
            return {
                "senior_id": senior_id,
                "enabled": False,
                "should_trigger_check_in": False,
                "reason": "HeatRisk checks are disabled for this senior.",
            }

        provider = settings.heat_risk_provider.lower().strip()

        if provider == "nws":
            observation = self._get_nws_heat_risk(
                senior_id=senior_id,
                latitude=heat_settings["latitude"],
                longitude=heat_settings["longitude"],
            )
        else:
            observation = self._get_manual_heat_risk(
                senior_id=senior_id,
                latitude=heat_settings["latitude"],
                longitude=heat_settings["longitude"],
            )

        threshold = heat_settings["trigger_threshold"]
        should_trigger = observation["heat_risk_value"] >= threshold

        return {
            "senior_id": senior_id,
            "heat_settings": heat_settings,
            "observation": observation,
            "trigger_threshold": threshold,
            "should_trigger_check_in": should_trigger,
            "reason": (
                f"HeatRisk {observation['heat_risk_value']} "
                f"({observation['heat_risk_label']}) "
                f"{'meets' if should_trigger else 'does not meet'} "
                f"threshold {threshold} ({heat_risk_label(threshold)})."
            ),
        }

    def _save_observation(
        self,
        senior_id: int | None,
        provider: str,
        latitude: float | None,
        longitude: float | None,
        heat_risk_value: int,
        source_url: str | None,
        raw_response: dict[str, Any],
    ) -> dict[str, Any]:
        with SessionLocal() as db:
            row = HeatRiskObservation(
                senior_id=senior_id,
                provider=provider,
                latitude=latitude,
                longitude=longitude,
                heat_risk_value=heat_risk_value,
                heat_risk_label=heat_risk_label(heat_risk_value),
                source_url=source_url,
                raw_response_json=json.dumps(raw_response, ensure_ascii=False),
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            return _observation_to_dict(row)

    def _get_manual_heat_risk(
        self,
        senior_id: int,
        latitude: float | None,
        longitude: float | None,
    ) -> dict[str, Any]:
        value = _coerce_heat_risk_value(settings.manual_heat_risk_value)

        return self._save_observation(
            senior_id=senior_id,
            provider="manual",
            latitude=latitude,
            longitude=longitude,
            heat_risk_value=value,
            source_url=None,
            raw_response={
                "manual_heat_risk_value": value,
                "note": "Manual HeatRisk mode is being used for local development.",
            },
        )

    def _get_nws_heat_risk(
        self,
        senior_id: int,
        latitude: float | None,
        longitude: float | None,
    ) -> dict[str, Any]:
        if latitude is None or longitude is None:
            raise ValueError("Latitude and longitude are required for NWS HeatRisk lookup.")

        params = {
            "f": "json",
            "geometry": json.dumps({
                "x": longitude,
                "y": latitude,
                "spatialReference": {"wkid": 4326},
            }),
            "geometryType": "esriGeometryPoint",
            "returnFirstValueOnly": "true",
            "outFields": "*",
        }

        url = f"{NWS_HEATRISK_IMAGE_SERVER}/getSamples?{urlencode(params)}"

        request = Request(
            url,
            headers={
                "User-Agent": settings.nws_user_agent,
                "Accept": "application/json",
            },
        )

        with urlopen(request, timeout=20) as response:
            raw_text = response.read().decode("utf-8")

        data = json.loads(raw_text)

        samples = data.get("samples") or []

        if not samples:
            raise ValueError("NWS HeatRisk service returned no samples for this location.")

        sample = samples[0]

        raw_value = sample.get("value")

        if raw_value is None:
            raise ValueError("NWS HeatRisk service returned a sample without a value.")

        value = _coerce_heat_risk_value(raw_value)

        return self._save_observation(
            senior_id=senior_id,
            provider="nws",
            latitude=latitude,
            longitude=longitude,
            heat_risk_value=value,
            source_url=url,
            raw_response=data,
        )

    def _local_date_for_heat_settings(
        self,
        heat_settings: dict[str, Any],
    ) -> str:
        tz = ZoneInfo(heat_settings["timezone"])
        now_local = datetime.now(timezone.utc).astimezone(tz)
        return now_local.date().isoformat()

    def _already_triggered_today(
        self,
        senior_id: int,
        local_date: str,
    ) -> bool:
        with SessionLocal() as db:
            row = (
                db.query(HeatTriggeredCall)
                .filter(HeatTriggeredCall.senior_id == senior_id)
                .filter(HeatTriggeredCall.local_date == local_date)
                .filter(HeatTriggeredCall.started.is_(True))
                .first()
            )

            return row is not None

    def _record_heat_triggered_call(
        self,
        senior_id: int,
        local_date: str,
        heat_risk_value: int,
        started: bool,
        senior_call_sid: str | None,
        reason: str | None,
    ) -> dict[str, Any]:
        with SessionLocal() as db:
            row = HeatTriggeredCall(
                senior_id=senior_id,
                local_date=local_date,
                heat_risk_value=heat_risk_value,
                heat_risk_label=heat_risk_label(heat_risk_value),
                started=started,
                senior_call_sid=senior_call_sid,
                reason=reason,
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            return _triggered_call_to_dict(row)

    def run_heat_risk_checks(self) -> dict[str, Any]:
        """
        Checks all enabled senior heat settings.

        If HeatRisk >= threshold and that senior has not already received
        a heat-triggered check-in today, start a profile-based call.
        """

        checked_at = datetime.now(timezone.utc)
        results = []

        heat_settings_list = self.list_heat_settings()

        for heat_settings in heat_settings_list:
            senior_id = heat_settings["senior_id"]

            if not heat_settings["enabled"]:
                results.append({
                    "senior_id": senior_id,
                    "started": False,
                    "reason": "HeatRisk checks disabled.",
                })
                continue

            local_date = self._local_date_for_heat_settings(heat_settings)

            if self._already_triggered_today(senior_id, local_date):
                results.append({
                    "senior_id": senior_id,
                    "started": False,
                    "reason": f"Heat-triggered check already started on {local_date}.",
                })
                continue

            try:
                risk_result = self.get_current_heat_risk_for_senior(senior_id)
            except Exception as exc:
                results.append({
                    "senior_id": senior_id,
                    "started": False,
                    "reason": f"HeatRisk lookup failed: {str(exc)}",
                })
                continue

            observation = risk_result["observation"]
            heat_value = observation["heat_risk_value"]

            if not risk_result["should_trigger_check_in"]:
                results.append({
                    "senior_id": senior_id,
                    "started": False,
                    "heat_risk_value": heat_value,
                    "heat_risk_label": observation["heat_risk_label"],
                    "reason": risk_result["reason"],
                })
                continue

            senior = profile_service.get_senior(senior_id)

            if not senior:
                self._record_heat_triggered_call(
                    senior_id=senior_id,
                    local_date=local_date,
                    heat_risk_value=heat_value,
                    started=False,
                    senior_call_sid=None,
                    reason="Senior profile not found.",
                )

                results.append({
                    "senior_id": senior_id,
                    "started": False,
                    "reason": "Senior profile not found.",
                })
                continue

            caregiver = profile_service.get_primary_caregiver_for_senior(senior_id)

            try:
                call = twilio_service.start_senior_speech_check_call(
                    senior_id=senior["id"],
                    senior_phone_number=senior["phone_number"],
                )

                session = profile_service.create_check_in_call_session(
                    senior=senior,
                    caregiver=caregiver,
                    senior_call_sid=call.sid,
                )

                trigger_record = self._record_heat_triggered_call(
                    senior_id=senior_id,
                    local_date=local_date,
                    heat_risk_value=heat_value,
                    started=True,
                    senior_call_sid=call.sid,
                    reason=risk_result["reason"],
                )

                results.append({
                    "senior_id": senior_id,
                    "senior_name": senior["name"],
                    "started": True,
                    "call_sid": call.sid,
                    "heat_risk_value": heat_value,
                    "heat_risk_label": observation["heat_risk_label"],
                    "reason": risk_result["reason"],
                    "session": session,
                    "trigger_record": trigger_record,
                })

            except Exception as exc:
                trigger_record = self._record_heat_triggered_call(
                    senior_id=senior_id,
                    local_date=local_date,
                    heat_risk_value=heat_value,
                    started=False,
                    senior_call_sid=None,
                    reason=str(exc),
                )

                results.append({
                    "senior_id": senior_id,
                    "senior_name": senior["name"],
                    "started": False,
                    "heat_risk_value": heat_value,
                    "heat_risk_label": observation["heat_risk_label"],
                    "reason": str(exc),
                    "trigger_record": trigger_record,
                })

        return {
            "checked_at": checked_at.isoformat(),
            "provider": settings.heat_risk_provider,
            "started_count": len([item for item in results if item.get("started")]),
            "results": results,
        }


heat_risk_service = HeatRiskService()