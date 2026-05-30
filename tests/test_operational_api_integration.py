import json

from app.db.database import SessionLocal
from app.db.models import (
    CheckIn,
    ConversationInsight,
    OperatorAction,
    OperatorActionEvidence,
    TranscriptTurn,
)


def _create_senior(client, auth_headers, *, name: str = "Test Senior") -> dict:
    response = client.post(
        "/seniors",
        headers=auth_headers,
        json={
            "name": name,
            "phone_number": "+15550109999",
            "preferred_language": "en-US",
            "notes": "Integration test senior.",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["senior"]


def test_demographics_and_heat_settings_round_trip(client, auth_headers):
    senior = _create_senior(client, auth_headers)
    senior_id = senior["id"]

    missing_demographics = client.get(
        f"/seniors/{senior_id}/demographics",
        headers=auth_headers,
    )
    assert missing_demographics.status_code == 404

    demographics_response = client.put(
        f"/seniors/{senior_id}/demographics",
        headers=auth_headers,
        json={
            "date_of_birth": None,
            "age_years": 80,
            "gender": "female",
            "pronouns": "she/her",
            "primary_language": "en-US",
            "notes": "Uses a cane.",
        },
    )

    assert demographics_response.status_code == 200, demographics_response.text

    demographics = demographics_response.json()["demographics"]

    assert demographics["senior_id"] == senior_id
    assert demographics["date_of_birth"] is None
    assert demographics["age_years"] == 80
    assert demographics["gender"] == "female"
    assert demographics["pronouns"] == "she/her"
    assert demographics["primary_language"] == "en-US"
    assert demographics["notes"] == "Uses a cane."

    read_demographics = client.get(
        f"/seniors/{senior_id}/demographics",
        headers=auth_headers,
    )

    assert read_demographics.status_code == 200, read_demographics.text
    assert read_demographics.json()["demographics"]["age_years"] == 80

    missing_heat_settings = client.get(
        f"/seniors/{senior_id}/heat-settings",
        headers=auth_headers,
    )
    assert missing_heat_settings.status_code == 404

    heat_settings_response = client.put(
        f"/seniors/{senior_id}/heat-settings",
        headers=auth_headers,
        json={
            "enabled": True,
            "latitude": 38.5816,
            "longitude": -121.4944,
            "city": "Sacramento",
            "state": "CA",
            "zip_code": "95814",
            "timezone": "America/Los_Angeles",
            "trigger_threshold": 2,
        },
    )

    assert heat_settings_response.status_code == 200, heat_settings_response.text

    heat_settings = heat_settings_response.json()["heat_settings"]

    assert heat_settings["senior_id"] == senior_id
    assert heat_settings["enabled"] is True
    assert heat_settings["city"] == "Sacramento"
    assert heat_settings["state"] == "CA"
    assert heat_settings["trigger_threshold"] == 2

    read_heat_settings = client.get(
        f"/seniors/{senior_id}/heat-settings",
        headers=auth_headers,
    )

    assert read_heat_settings.status_code == 200, read_heat_settings.text
    assert read_heat_settings.json()["heat_settings"]["zip_code"] == "95814"

    heat_risk_response = client.get(
        f"/seniors/{senior_id}/heat-risk",
        headers=auth_headers,
    )

    assert heat_risk_response.status_code == 200, heat_risk_response.text

    heat_risk = heat_risk_response.json()["result"]

    assert heat_risk["senior_id"] == senior_id
    assert heat_risk["observation"]["provider"] == "manual"
    assert heat_risk["observation"]["heat_risk_value"] == 2
    assert heat_risk["observation"]["heat_risk_label"] == "Moderate"
    assert heat_risk["trigger_threshold"] == 2
    assert heat_risk["should_trigger_check_in"] is True


def test_support_network_round_trip(client, auth_headers):
    senior = _create_senior(client, auth_headers)
    senior_id = senior["id"]

    empty_network_response = client.get(
        f"/seniors/{senior_id}/support-network",
        headers=auth_headers,
    )

    assert empty_network_response.status_code == 200, empty_network_response.text

    empty_network = empty_network_response.json()

    assert empty_network["senior_id"] == senior_id
    assert empty_network["plan"] is None
    assert empty_network["support_contacts"] == []
    assert empty_network["steps"] == []

    plan_response = client.put(
        f"/seniors/{senior_id}/escalation-plan",
        headers=auth_headers,
        json={
            "living_situation": "Lives alone",
            "support_mode": "Family supported",
            "allow_operator_review": True,
            "allow_wellness_check": True,
            "allow_emergency_escalation": False,
            "notes": "Call daughter first during heat events.",
        },
    )

    assert plan_response.status_code == 200, plan_response.text

    plan = plan_response.json()["plan"]

    assert plan["senior_id"] == senior_id
    assert plan["living_situation"] == "Lives alone"
    assert plan["support_mode"] == "Family supported"
    assert plan["notes"] == "Call daughter first during heat events."

    contact_response = client.post(
        f"/seniors/{senior_id}/support-contacts",
        headers=auth_headers,
        json={
            "name": "Ana Support",
            "phone_number": "+15550108888",
            "relationship": "Daughter",
            "contact_type": "family",
            "priority": 1,
            "can_receive_alerts": True,
            "is_emergency_contact": True,
            "notes": "Lives nearby.",
        },
    )

    assert contact_response.status_code == 200, contact_response.text

    contact = contact_response.json()["support_contact"]
    contact_id = contact["id"]

    assert contact["senior_id"] == senior_id
    assert contact["name"] == "Ana Support"
    assert contact["relationship"] == "Daughter"
    assert contact["is_active"] is True

    update_contact_response = client.patch(
        f"/support-contacts/{contact_id}",
        headers=auth_headers,
        json={
            "relationship": "Daughter - primary",
            "priority": 2,
            "notes": "Updated by integration test.",
        },
    )

    assert update_contact_response.status_code == 200, update_contact_response.text

    updated_contact = update_contact_response.json()["support_contact"]

    assert updated_contact["relationship"] == "Daughter - primary"
    assert updated_contact["priority"] == 2
    assert updated_contact["notes"] == "Updated by integration test."

    step_response = client.post(
        f"/seniors/{senior_id}/escalation-steps",
        headers=auth_headers,
        json={
            "step_order": 1,
            "trigger_level": "major",
            "action_type": "message_support",
            "target_contact_id": contact_id,
            "instructions": "Ask Ana to check in within 15 minutes.",
        },
    )

    assert step_response.status_code == 200, step_response.text

    step = step_response.json()["step"]

    assert step["step_order"] == 1
    assert step["trigger_level"] == "major"
    assert step["action_type"] == "message_support"
    assert step["target_contact_id"] == contact_id
    assert step["is_active"] is True

    network_response = client.get(
        f"/seniors/{senior_id}/support-network",
        headers=auth_headers,
    )

    assert network_response.status_code == 200, network_response.text

    network = network_response.json()

    assert network["plan"]["living_situation"] == "Lives alone"
    assert len(network["support_contacts"]) == 1
    assert network["support_contacts"][0]["id"] == contact_id
    assert len(network["steps"]) == 1
    assert network["steps"][0]["id"] == step["id"]

    deactivate_response = client.delete(
        f"/support-contacts/{contact_id}",
        headers=auth_headers,
    )

    assert deactivate_response.status_code == 200, deactivate_response.text
    assert deactivate_response.json()["support_contact"]["is_active"] is False

    network_after_deactivate = client.get(
        f"/seniors/{senior_id}/support-network",
        headers=auth_headers,
    )

    assert network_after_deactivate.status_code == 200, network_after_deactivate.text
    assert network_after_deactivate.json()["support_contacts"] == []


def test_operator_actions_round_trip(client, auth_headers):
    senior = _create_senior(client, auth_headers)
    senior_id = senior["id"]

    create_response = client.post(
        f"/seniors/{senior_id}/operator-actions",
        headers=auth_headers,
        json={
            "action_type": "wellness_check",
            "status": "requested",
            "reason": "Senior is in a major heat-risk zone.",
            "note": "Please check on hydration.",
            "created_by": "integration-test",
        },
    )

    assert create_response.status_code == 200, create_response.text

    action = create_response.json()["action"]
    action_id = action["id"]

    assert action["senior_id"] == senior_id
    assert action["action_type"] == "wellness_check"
    assert action["status"] == "requested"
    assert action["reason"] == "Senior is in a major heat-risk zone."
    assert action["created_by"] == "integration-test"

    list_response = client.get(
        f"/seniors/{senior_id}/operator-actions",
        headers=auth_headers,
    )

    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["senior_id"] == senior_id
    assert len(list_response.json()["items"]) == 1

    pending_response = client.get(
        "/operator-actions/pending",
        headers=auth_headers,
    )

    assert pending_response.status_code == 200, pending_response.text
    assert [item["id"] for item in pending_response.json()["items"]] == [action_id]

    filtered_response = client.get(
        "/operator-actions?status=requested",
        headers=auth_headers,
    )

    assert filtered_response.status_code == 200, filtered_response.text
    assert [item["id"] for item in filtered_response.json()["items"]] == [action_id]

    update_response = client.patch(
        f"/operator-actions/{action_id}",
        headers=auth_headers,
        json={
            "status": "completed",
            "note": "Operator confirmed support contact will visit.",
        },
    )

    assert update_response.status_code == 200, update_response.text

    updated_action = update_response.json()["action"]

    assert updated_action["status"] == "completed"
    assert updated_action["note"] == "Operator confirmed support contact will visit."

    pending_after_update = client.get(
        "/operator-actions/pending",
        headers=auth_headers,
    )

    assert pending_after_update.status_code == 200, pending_after_update.text
    assert pending_after_update.json()["items"] == []


def test_check_in_review_returns_transcript_insight_and_operator_evidence(
    client,
    auth_headers,
):
    senior = _create_senior(client, auth_headers)
    senior_id = senior["id"]

    with SessionLocal() as db:
        check_in = CheckIn(
            source="integration_test",
            senior_phone_number=senior["phone_number"],
            senior_call_sid="CA_integration_check_in_001",
            senior_call_status="completed",
            senior_call_duration_seconds=73,
            transcript="assistant: Hello\nsenior: I feel warm but okay",
            speech_confidence="0.91",
            risk_level="yellow",
            reported_symptoms_json=json.dumps(["warm"]),
            red_flags_json=json.dumps([]),
            orientation_concern=False,
            escalation_needed=True,
            caregiver_summary="Senior reported mild heat discomfort.",
            recommended_action="Ask support contact to check in.",
            confidence_notes="Integration test confidence notes.",
            analyzer="integration_test",
            raw_analysis_json=json.dumps({"source": "test"}),
            caregiver_alert_required=False,
            caregiver_alert_sent=False,
        )
        db.add(check_in)
        db.commit()
        db.refresh(check_in)

        transcript_turn_1 = TranscriptTurn(
            senior_id=senior_id,
            check_in_id=check_in.id,
            senior_call_sid=check_in.senior_call_sid,
            turn_index=0,
            speaker="assistant",
            text="Hello, this is a quick heat safety check.",
        )
        transcript_turn_2 = TranscriptTurn(
            senior_id=senior_id,
            check_in_id=check_in.id,
            senior_call_sid=check_in.senior_call_sid,
            turn_index=1,
            speaker="senior",
            text="I feel warm but okay.",
        )

        db.add(transcript_turn_1)
        db.add(transcript_turn_2)
        db.commit()

        insight = ConversationInsight(
            senior_id=senior_id,
            check_in_id=check_in.id,
            senior_call_sid=check_in.senior_call_sid,
            safety_risk_level="yellow",
            safety_confidence=0.72,
            safety_summary="Mild heat discomfort reported.",
            safety_escalation_needed=True,
            safety_reason_codes_json=json.dumps(["heat_discomfort"]),
            relationship_summary="Senior completed a brief welfare conversation.",
            mood_label="neutral",
            loneliness_signal="low",
            topics_discussed_json=json.dumps(["heat safety"]),
            follow_up_suggestions_json=json.dumps(["Ask whether they had water."]),
            recommended_actions_json=json.dumps(
                [
                    {
                        "action_type": "message_support",
                        "reason": "Support contact should check in.",
                        "target_contact_id": None,
                    }
                ]
            ),
            memory_candidates_json=json.dumps([]),
            analyzer="integration_test",
            raw_analysis_json=json.dumps({"source": "test"}),
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)

        action = OperatorAction(
            senior_id=senior_id,
            action_type="message_support",
            status="requested",
            reason="Support contact should check in.",
            note="Created from check-in review integration test.",
            target_contact_id=None,
            created_by="integration_test",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        evidence = OperatorActionEvidence(
            operator_action_id=action.id,
            senior_id=senior_id,
            check_in_id=check_in.id,
            conversation_insight_id=insight.id,
            source="integration_test",
            reason="Mild heat discomfort was reported.",
        )
        db.add(evidence)
        db.commit()

        check_in_id = check_in.id
        insight_id = insight.id
        action_id = action.id

    response = client.get(
        f"/check-ins/{check_in_id}/review",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text

    review = response.json()

    assert review["check_in"]["id"] == check_in_id
    assert review["check_in"]["risk_level"] == "yellow"
    assert review["check_in"]["reported_symptoms"] == ["warm"]
    assert review["senior"]["id"] == senior_id
    assert review["senior"]["name"] == senior["name"]

    assert review["insight"]["id"] == insight_id
    assert review["insight"]["safety_risk_level"] == "yellow"
    assert review["insight"]["topics_discussed"] == ["heat safety"]
    assert review["insight"]["follow_up_suggestions"] == [
        "Ask whether they had water."
    ]

    assert len(review["transcript_turns"]) == 2
    assert review["transcript_turns"][0]["speaker"] == "assistant"
    assert review["transcript_turns"][1]["speaker"] == "senior"

    assert len(review["operator_actions"]) == 1
    assert review["operator_actions"][0]["id"] == action_id
    assert review["operator_actions"][0]["action_type"] == "message_support"

    assert len(review["operator_action_evidence"]) == 1
    assert review["operator_action_evidence"][0]["operator_action_id"] == action_id
    assert review["operator_action_evidence"][0]["conversation_insight_id"] == insight_id