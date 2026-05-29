from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.profile_service import profile_service

from app.services.support_network_service import support_network_service

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
    location = DISPLAY_LOCATIONS[index % len(DISPLAY_LOCATIONS)]
    support_context = _support_context_for_senior(raw, location)

    name = raw.get("name") or FALLBACK_NAMES[index % len(FALLBACK_NAMES)]
    senior_id = raw.get("id") or _slugify(name)

    return {
        "id": senior_id,
        "name": name,
        "age": location["age"],
        "gender": location["gender"],
        "location": location["location"],
        "city": location["city"],
        "state": location["state"],
        "lat": location["lat"],
        "lng": location["lng"],
        "phone": raw.get("phone_number") or "(555) 555-0198",
        "address": f"1234 Desert View Dr, {location['location']} 85016",
        "preferredContactTime": "9:00 AM – 7:00 PM",
        "medicalNotes": raw.get("notes")
        or "Monitor hydration, heat exposure, and unusual fatigue.",
        "emergencyContact": "See support network",
        "heatRisk": location["heatRisk"],
        "status": location["status"],
        "latestCheckIn": "Today, 10:18 AM",
        "assignedCaregiver": support_context["assignedSupport"],
        "recommendedAction": location["recommendedAction"],
        "isActive": raw.get("is_active", True),
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


def _timeline() -> list[dict[str, Any]]:
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
            return {
                "senior": senior,
                "timeline": _timeline(),
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