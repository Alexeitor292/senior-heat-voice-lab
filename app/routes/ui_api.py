from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.profile_service import profile_service

from app.services.support_network_service import support_network_service

from app.services.heat_risk_service import heat_risk_service

from app.services.operational_status_service import operational_status_service

from app.services.demographics_service import demographics_service

from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/ui-api", tags=["UI API"])


DISPLAY_LOCATIONS = [
    {
        "city": "Phoenix",
        "state": "AZ",
        "location": "Phoenix, AZ",
        "lat": 33.45,
        "lng": -112.07,
        "heatRisk": "High",
        "status": "Urgent",
        "age": 79,
        "gender": "Female",
        "recommendedAction": "Operator review + wellness check",
        "livingSituation": "Lives alone",
        "supportMode": "Operator monitored",
        "supportContactCount": 0,
        "hasSupportContact": False,
        "escalationPlanSummary": "No support contact listed. Route high-risk cases to operator review.",
    },
    {
        "city": "San Antonio",
        "state": "TX",
        "location": "San Antonio, TX",
        "lat": 29.42,
        "lng": -98.49,
        "heatRisk": "High",
        "status": "Urgent",
        "age": 82,
        "gender": "Male",
        "recommendedAction": "Call daughter, then retry senior",
        "livingSituation": "Lives with family",
        "supportMode": "Family supported",
        "supportContactCount": 2,
        "hasSupportContact": True,
        "escalationPlanSummary": "Contact family first. Escalate to operator if no response.",
    },
    {
        "city": "New Orleans",
        "state": "LA",
        "location": "New Orleans, LA",
        "lat": 29.95,
        "lng": -90.07,
        "heatRisk": "Moderate",
        "status": "Watch",
        "age": 86,
        "gender": "Female",
        "recommendedAction": "Call senior",
        "livingSituation": "Lives alone",
        "supportMode": "Self-managed",
        "supportContactCount": 1,
        "hasSupportContact": True,
        "escalationPlanSummary": "Retry senior first. If no response, notify emergency contact.",
    },
    {
        "city": "Miami",
        "state": "FL",
        "location": "Miami, FL",
        "lat": 25.77,
        "lng": -80.19,
        "heatRisk": "High",
        "status": "Watch",
        "age": 74,
        "gender": "Male",
        "recommendedAction": "Routine check-in",
        "livingSituation": "Senior community",
        "supportMode": "Facility supported",
        "supportContactCount": 1,
        "hasSupportContact": True,
        "escalationPlanSummary": "Notify facility front desk for urgent cases.",
    },
    {
        "city": "Atlanta",
        "state": "GA",
        "location": "Atlanta, GA",
        "lat": 33.75,
        "lng": -84.39,
        "heatRisk": "Moderate",
        "status": "Stable",
        "age": 71,
        "gender": "Female",
        "recommendedAction": "Routine check-in",
        "livingSituation": "Lives with family",
        "supportMode": "Family supported",
        "supportContactCount": 1,
        "hasSupportContact": True,
        "escalationPlanSummary": "Notify listed family contact if risk increases.",
    },
    {
        "city": "Los Angeles",
        "state": "CA",
        "location": "Los Angeles, CA",
        "lat": 34.05,
        "lng": -118.24,
        "heatRisk": "Moderate",
        "status": "Safe",
        "age": 77,
        "gender": "Male",
        "recommendedAction": "No action needed",
        "livingSituation": "Lives alone",
        "supportMode": "Community supported",
        "supportContactCount": 1,
        "hasSupportContact": True,
        "escalationPlanSummary": "Community volunteer is first support contact.",
    },
    {
        "city": "Denver",
        "state": "CO",
        "location": "Denver, CO",
        "lat": 39.74,
        "lng": -104.99,
        "heatRisk": "Low",
        "status": "Safe",
        "age": 83,
        "gender": "Female",
        "recommendedAction": "No action needed",
        "livingSituation": "Assisted living",
        "supportMode": "Facility supported",
        "supportContactCount": 2,
        "hasSupportContact": True,
        "escalationPlanSummary": "Facility staff receives urgent alerts.",
    },
    {
        "city": "Chicago",
        "state": "IL",
        "location": "Chicago, IL",
        "lat": 41.85,
        "lng": -87.63,
        "heatRisk": "Low",
        "status": "Stable",
        "age": 78,
        "gender": "Male",
        "recommendedAction": "No action needed",
        "livingSituation": "Lives alone",
        "supportMode": "Operator monitored",
        "supportContactCount": 0,
        "hasSupportContact": False,
        "escalationPlanSummary": "Operator review required when risk reaches moderate.",
    },
    {
        "city": "Seattle",
        "state": "WA",
        "location": "Seattle, WA",
        "lat": 47.61,
        "lng": -122.33,
        "heatRisk": "Low",
        "status": "Safe",
        "age": 80,
        "gender": "Female",
        "recommendedAction": "No action needed",
        "livingSituation": "Lives with family",
        "supportMode": "Family supported",
        "supportContactCount": 2,
        "hasSupportContact": True,
        "escalationPlanSummary": "Family contact receives escalation alerts.",
    },
    {
        "city": "Houston",
        "state": "TX",
        "location": "Houston, TX",
        "lat": 29.76,
        "lng": -95.37,
        "heatRisk": "High",
        "status": "Watch",
        "age": 75,
        "gender": "Male",
        "recommendedAction": "Call senior",
        "livingSituation": "Lives alone",
        "supportMode": "Self-managed",
        "supportContactCount": 0,
        "hasSupportContact": False,
        "escalationPlanSummary": "No support contact listed. Retry senior, then operator review.",
    },
]


FALLBACK_NAMES = [
    "Eleanor Jennings",
    "Robert Martinez",
    "Lillian Carter",
    "James Wilson",
    "Helen Brooks",
    "George Chen",
    "Dorothy Hayes",
    "William Thomas",
    "Mary Johnson",
    "Frank Nguyen",
]


def _slugify(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")
    )

def _support_context_for_senior(
    raw: dict[str, Any],
    location: dict[str, Any],
) -> dict[str, Any]:
    fallback = {
        "assignedSupport": "Assigned Support",
        "livingSituation": location["livingSituation"],
        "supportMode": location["supportMode"],
        "supportContactCount": location["supportContactCount"],
        "hasSupportContact": location["hasSupportContact"],
        "escalationPlanSummary": location["escalationPlanSummary"],
    }

    raw_id = raw.get("id")

    try:
        senior_id = int(raw_id)
    except (TypeError, ValueError):
        return fallback

    network = support_network_service.get_support_network(senior_id)

    if not network:
        return fallback

    plan = network.get("plan")
    contacts = network.get("support_contacts", [])

    if not plan and not contacts:
        return fallback

    primary_contact = contacts[0] if contacts else None
    has_support_contact = bool(contacts)

    if primary_contact:
        assigned_support = primary_contact["name"]
    elif plan and plan.get("allow_operator_review"):
        assigned_support = "Operator Review"
    else:
        assigned_support = "No support contact"

    living_situation = (
        plan.get("living_situation")
        if plan and plan.get("living_situation")
        else fallback["livingSituation"]
    )

    support_mode = (
        plan.get("support_mode")
        if plan and plan.get("support_mode")
        else fallback["supportMode"]
    )

    if plan and plan.get("notes"):
        escalation_summary = plan["notes"]
    elif not has_support_contact:
        escalation_summary = (
            "No support contact listed. Route high-risk cases to operator review."
        )
    else:
        escalation_summary = "Contact support network according to priority order."

    return {
        "assignedSupport": assigned_support,
        "livingSituation": living_situation,
        "supportMode": support_mode,
        "supportContactCount": len(contacts),
        "hasSupportContact": has_support_contact,
        "escalationPlanSummary": escalation_summary,
    }

def _coerce_numeric_senior_id(raw: dict[str, Any]) -> int | None:
    raw_id = raw.get("id")

    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return None


def _city_state_label(city: str | None, state: str | None) -> str | None:
    if city and state:
        return f"{city}, {state}"

    if city:
        return city

    if state:
        return state

    return None


def _heat_settings_context_for_senior(
    raw: dict[str, Any],
    fallback_location: dict[str, Any],
) -> dict[str, Any]:
    """
    Prefer real SeniorHeatSettings for map/detail location fields.

    Fallback DISPLAY_LOCATIONS should only be used for demo seniors or real
    seniors that have not had heat settings configured yet.
    """
    senior_id = _coerce_numeric_senior_id(raw)

    fallback = {
        "city": fallback_location["city"],
        "state": fallback_location["state"],
        "zipCode": None,
        "location": fallback_location["location"],
        "lat": fallback_location["lat"],
        "lng": fallback_location["lng"],
        "timezone": "America/Los_Angeles",
        "address": f"Location on file: {fallback_location['location']}",
        "hasRealHeatSettings": False,
    }

    if senior_id is None:
        return fallback

    heat_settings = heat_risk_service.get_heat_settings(senior_id)

    if not heat_settings:
        return fallback

    city = heat_settings.get("city") or fallback["city"]
    state = heat_settings.get("state") or fallback["state"]
    zip_code = heat_settings.get("zip_code")

    location_label = _city_state_label(city, state) or fallback["location"]

    latitude = heat_settings.get("latitude")
    longitude = heat_settings.get("longitude")

    # The map requires lat/lng. If one is missing, keep fallback coordinates
    # but still use the real city/state text.
    if latitude is None or longitude is None:
        latitude = fallback["lat"]
        longitude = fallback["lng"]

    address_parts = [location_label]

    if zip_code:
        address_parts.append(str(zip_code))

    return {
        "city": city,
        "state": state,
        "zipCode": zip_code,
        "location": location_label,
        "lat": latitude,
        "lng": longitude,
        "timezone": heat_settings.get("timezone") or fallback["timezone"],
        "address": " ".join(address_parts),
        "hasRealHeatSettings": True,
    }

def _real_seniors_or_mock() -> list[dict[str, Any]]:
    real_seniors = profile_service.list_seniors()

    if real_seniors:
        return real_seniors

    return [
        {
            "id": _slugify(name),
            "name": name,
            "phone_number": f"(555) 555-01{index:02d}",
            "preferred_language": "en-US",
            "notes": "Mock UI profile.",
            "is_active": True,
        }
        for index, name in enumerate(FALLBACK_NAMES, start=1)
    ]


def _display_senior(raw: dict[str, Any], index: int) -> dict[str, Any]:
    fallback_location = DISPLAY_LOCATIONS[index % len(DISPLAY_LOCATIONS)]
    support_context = _support_context_for_senior(raw, fallback_location)
    heat_context = _heat_settings_context_for_senior(raw, fallback_location)
    demographics_context = _demographics_context_for_senior(raw, fallback_location)
    operational_status = operational_status_service.get_status_for_senior(
        senior=raw,
        has_support_contact=bool(support_context["hasSupportContact"]),
        fallback_heat_risk=fallback_location["heatRisk"],
        fallback_status=fallback_location["status"],
        fallback_recommended_action=fallback_location["recommendedAction"],
    )

    name = raw.get("name") or FALLBACK_NAMES[index % len(FALLBACK_NAMES)]
    senior_id = raw.get("id") or _slugify(name)

    return {
        "id": senior_id,
        "name": name,
        "age": demographics_context["age"],
        "gender": demographics_context["gender"],
        "dateOfBirth": demographics_context["dateOfBirth"],
        "pronouns": demographics_context["pronouns"],
        "primaryLanguage": demographics_context["primaryLanguage"],
        "hasRealDemographics": demographics_context["hasRealDemographics"],

        # Real location fields come from SeniorHeatSettings when available.
        "location": heat_context["location"],
        "city": heat_context["city"],
        "state": heat_context["state"],
        "zipCode": heat_context["zipCode"],
        "lat": heat_context["lat"],
        "lng": heat_context["lng"],
        "timezone": heat_context["timezone"],
        "hasRealHeatSettings": heat_context["hasRealHeatSettings"],

        "phone": raw.get("phone_number") or "(555) 555-0198",
        "address": heat_context["address"],
        "preferredContactTime": "9:00 AM - 7:00 PM",
        "medicalNotes": raw.get("notes")
        or "Monitor hydration, heat exposure, and unusual fatigue.",
        "emergencyContact": "See support network",

        # Risk/status still fall back to demo display data for now.
        # Next milestone can pull latest HeatRiskObservation.
        "heatRisk": operational_status["heatRisk"],
        "status": operational_status["status"],
        "latestCheckIn": operational_status["latestCheckIn"],
        "assignedCaregiver": support_context["assignedSupport"],
        "recommendedAction": operational_status["recommendedAction"],
        "heatRiskValue": operational_status["heatRiskValue"],
        "heatRiskSource": operational_status["heatRiskSource"],
        "latestCheckInRisk": operational_status["latestCheckInRisk"],
        "latestCheckInAt": operational_status["latestCheckInAt"],
        "escalationNeeded": operational_status.get("escalationNeeded", False),
        "orientationConcern": operational_status.get("orientationConcern", False),
        "isActive": raw.get("is_active", True),

        # Real support-network fields come from EscalationPlan/SupportContact when available.
        "livingSituation": support_context["livingSituation"],
        "supportMode": support_context["supportMode"],
        "supportContactCount": support_context["supportContactCount"],
        "hasSupportContact": support_context["hasSupportContact"],
        "escalationPlanSummary": support_context["escalationPlanSummary"],
    }


def _display_seniors() -> list[dict[str, Any]]:
    return [
        _display_senior(raw, index)
        for index, raw in enumerate(_real_seniors_or_mock())
    ]


def _summary(seniors: list[dict[str, Any]]) -> dict[str, int]:
    need_outreach = len([
        senior for senior in seniors
        if senior["status"] in {"Watch", "Urgent"}
    ])

    critical = len([
        senior for senior in seniors
        if senior["status"] == "Urgent"
    ])

    return {
        "seniorsMonitored": len(seniors),
        "supervisedSeniors": len(seniors),
        "needOutreach": need_outreach,
        "needOutreachToday": need_outreach,
        "criticalAlerts": critical,
        "critical": critical,
    }


def _urgent_outreach(seniors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    urgent = [
        senior for senior in seniors
        if senior["status"] in {"Urgent", "Watch"}
    ]

    return [
        {
            "seniorId": senior["id"],
            "name": senior["name"],
            "age": senior["age"],
            "location": senior["location"],
            "time": ["9:54 AM", "9:47 AM", "9:31 AM"][index % 3],
            "risk": senior["heatRisk"],
            "status": senior["status"],
            "supportMode": senior.get("supportMode"),
            "hasSupportContact": senior.get("hasSupportContact"),
        }
        for index, senior in enumerate(urgent[:3])
    ]


def _alerts(seniors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    urgent = _urgent_outreach(seniors)

    return [
        {
            "id": f"alert-{index + 1}",
            "seniorId": item["seniorId"],
            "seniorName": item["name"],
            "seniorAge": item["age"],
            "location": item["location"],
            "type": [
                "Extreme heat risk",
                "Missed check-in",
                "Wellness check needed",
            ][index % 3],
            "severity": "High" if item["risk"] == "High" else item["risk"],
            "message": "Senior needs outreach due to elevated heat conditions.",
            "time": item["time"],
            "acknowledged": False,
        }
        for index, item in enumerate(urgent)
    ]


def _schedule(seniors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = seniors[:3]

    return [
        {
            "time": ["9:30 AM", "10:30 AM", "1:00 PM"][index],
            "type": "Wellness Visit" if index == 2 else "Check-in Call",
            "seniorName": f"{senior['name']}, {senior['age']}",
            "location": senior["location"],
        }
        for index, senior in enumerate(selected)
    ]


def _priorities(seniors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized = [
        senior for senior in seniors
        if senior["status"] in {"Urgent", "Watch"}
    ][:3]

    return [
        {
            "rank": index + 1,
            "seniorId": senior["id"],
            "seniorName": senior["name"],
            "age": senior["age"],
            "location": senior["location"],
            "risk": senior["heatRisk"],
            "action": senior["recommendedAction"],
        }
        for index, senior in enumerate(prioritized)
    ]


def _fallback_timeline() -> list[dict[str, Any]]:
    return [
        {
            "id": "timeline-1",
            "type": "check-in",
            "title": "Check-in received",
            "description": "Senior reported they are doing well.",
            "time": "10:18 AM",
            "date": "Today",
            "status": "success",
        },
        {
            "id": "timeline-2",
            "type": "call-attempt",
            "title": "Call attempt",
            "description": "No answer. Left voicemail.",
            "time": "9:42 AM",
            "date": "Today",
            "status": "missed",
        },
        {
            "id": "timeline-3",
            "type": "check-in",
            "title": "Check-in received",
            "description": "Senior reported staying indoors and hydrated.",
            "time": "6:05 PM",
            "date": "Yesterday",
            "status": "success",
        },
        {
            "id": "timeline-4",
            "type": "note",
            "title": "Note added",
            "description": "Support contact reported grocery delivery completed.",
            "time": "4:15 PM",
            "date": "Yesterday",
            "status": "info",
        },
        {
            "id": "timeline-5",
            "type": "call-attempt",
            "title": "Call attempt",
            "description": "Spoke with senior. They were feeling okay.",
            "time": "9:11 AM",
            "date": "May 27",
            "status": "success",
        },
    ]

def _heat_check(senior: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"live-{senior['id']}",
        "seniorId": senior["id"],
        "seniorName": senior["name"],
        "phone": senior["phone"],
        "location": senior["location"],
        "callDuration": "02:47",
        "status": "active",
        "transcript": [
            {
                "speaker": "Agent",
                "name": "Agent",
                "text": "Hi, this is Sarah with the Heat Check team. How are you feeling today?",
                "time": "10:16 AM",
            },
            {
                "speaker": "Senior",
                "name": senior["name"],
                "text": "I'm feeling okay... just a little tired. It's been pretty hot in here.",
                "time": "10:16 AM",
            },
            {
                "speaker": "Agent",
                "name": "Agent",
                "text": "Have you had something to drink today?",
                "time": "10:17 AM",
            },
            {
                "speaker": "Senior",
                "name": senior["name"],
                "text": "Not much. Just some coffee this morning.",
                "time": "10:17 AM",
            },
        ],
        "riskSummary": {
            "hydrationConcern": "Elevated",
            "confusionIndicator": "Low",
            "currentHeatRisk": senior["heatRisk"],
            "score": 8.2 if senior["heatRisk"] == "High" else 5.8,
        },
        "recommendedAction": senior["recommendedAction"],
        "weather": "104°F Sunny",
        "lastCheckIn": senior["latestCheckIn"],
    }

def _demographics_context_for_senior(
    raw: dict[str, Any],
    fallback_location: dict[str, Any],
) -> dict[str, Any]:
    fallback = {
        "age": fallback_location["age"],
        "gender": fallback_location["gender"],
        "dateOfBirth": None,
        "pronouns": None,
        "primaryLanguage": raw.get("preferred_language") or "en-US",
        "hasRealDemographics": False,
    }

    senior_id = _coerce_numeric_senior_id(raw)

    if senior_id is None:
        return fallback

    demographics = demographics_service.get_demographics(senior_id)

    if not demographics:
        return fallback

    return {
        "age": demographics.get("age_years") or fallback["age"],
        "gender": demographics.get("gender") or fallback["gender"],
        "dateOfBirth": demographics.get("date_of_birth"),
        "pronouns": demographics.get("pronouns"),
        "primaryLanguage": demographics.get("primary_language") or fallback["primaryLanguage"],
        "hasRealDemographics": True,
    }

@router.get("/map")
def get_map_view():
    seniors = _display_seniors()
    selected = seniors[0] if seniors else None

    return {
        "summary": _summary(seniors),
        "seniors": seniors,
        "selectedSeniorId": selected["id"] if selected else None,
        "urgentOutreach": _urgent_outreach(seniors),
    }


@router.get("/dashboard")
def get_dashboard_view():
    seniors = _display_seniors()

    return {
        "summary": _summary(seniors),
        "priorities": _priorities(seniors),
        "schedule": _schedule(seniors),
        "alerts": _alerts(seniors),
        "trendData": [
            {"date": "May 23", "value": 1.2},
            {"date": "May 24", "value": 1.4},
            {"date": "May 25", "value": 2.0},
            {"date": "May 26", "value": 2.7},
            {"date": "May 27", "value": 2.9},
            {"date": "May 28", "value": 3.5},
            {"date": "May 29", "value": 4.1},
        ],
    }


@router.get("/seniors")
def list_ui_seniors():
    return {
        "items": _display_seniors(),
    }


@router.get("/seniors/{senior_id}")
def get_ui_senior(senior_id: str):
    seniors = _display_seniors()

    for senior in seniors:
        if str(senior["id"]) == senior_id or _slugify(senior["name"]) == senior_id:
            timeline = None

            try:
                timeline = timeline_service.get_timeline_for_senior(
                    senior_id=int(senior["id"]),
                    limit=12,
                )
            except (TypeError, ValueError):
                timeline = None

            return {
                "senior": senior,
                "timeline": timeline or _fallback_timeline(),
            }

    raise HTTPException(status_code=404, detail="Senior not found.")


@router.get("/alerts")
def list_ui_alerts():
    seniors = _display_seniors()
    return {
        "items": _alerts(seniors),
    }


@router.get("/heat-checks/{call_id}")
def get_ui_heat_check(call_id: str):
    seniors = _display_seniors()

    if call_id.startswith("live-"):
        senior_key = call_id.removeprefix("live-")
    else:
        senior_key = call_id

    for senior in seniors:
        if str(senior["id"]) == senior_key or _slugify(senior["name"]) == senior_key:
            return _heat_check(senior)

    if seniors:
        return _heat_check(seniors[0])

    raise HTTPException(status_code=404, detail="Heat check not found.")