from twilio.rest import Client

from app.config import settings


class TwilioService:
    def __init__(self):
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )

    def _base_url(self) -> str:
        """
        Avoid double slashes if PUBLIC_BASE_URL accidentally has a trailing slash.
        """
        return settings.public_base_url.rstrip("/")

    def start_test_call(self):
        """
        Step 1 and Step 2 call.

        Starts a Twilio outbound call to the test phone number.
        Twilio fetches TwiML instructions from /twilio/voice/heat-check.
        """

        base_url = self._base_url()

        voice_webhook_url = f"{base_url}/twilio/voice/heat-check"
        status_callback_url = f"{base_url}/twilio/status"

        call = self.client.calls.create(
            to=settings.test_phone_number,
            from_=settings.twilio_phone_number,
            url=voice_webhook_url,
            method="POST",
            status_callback=status_callback_url,
            status_callback_method="POST",
            status_callback_event=[
                "initiated",
                "ringing",
                "answered",
                "completed"
            ],
        )

        return call

    def start_speech_test_call(self):
        """
        Step 3, Step 4, and Step 5 call.

        Starts a Twilio outbound call that asks the test user
        to answer by speaking instead of pressing a keypad digit.
        """

        base_url = self._base_url()

        voice_webhook_url = f"{base_url}/twilio/voice/heat-check-speech"
        status_callback_url = f"{base_url}/twilio/status"

        call = self.client.calls.create(
            to=settings.test_phone_number,
            from_=settings.twilio_phone_number,
            url=voice_webhook_url,
            method="POST",
            status_callback=status_callback_url,
            status_callback_method="POST",
            status_callback_event=[
                "initiated",
                "ringing",
                "answered",
                "completed"
            ],
        )

        return call

    def start_caregiver_voice_alert_call(
        self,
        caregiver_phone_number: str,
        alert_id: str
    ):
        """
        Starts an outbound voice call to the caregiver.

        The alert_id points to an in-memory alert payload that the
        caregiver alert webhook will read and speak out loud.
        """

        base_url = self._base_url()

        voice_webhook_url = (
            f"{base_url}/twilio/voice/caregiver-alert"
            f"?alert_id={alert_id}"
        )

        status_callback_url = f"{base_url}/twilio/status"

        call = self.client.calls.create(
            to=caregiver_phone_number,
            from_=settings.twilio_phone_number,
            url=voice_webhook_url,
            method="POST",
            status_callback=status_callback_url,
            status_callback_method="POST",
            status_callback_event=[
                "initiated",
                "ringing",
                "answered",
                "completed"
            ],
        )

        return call

    def send_sms(self, to_phone_number: str, message: str):
        """
        Keeps SMS available for later production testing.

        For now, caregiver alerts will use voice calls because
        SMS deliverability requires additional Twilio compliance setup.
        """

        sms = self.client.messages.create(
            to=to_phone_number,
            from_=settings.twilio_phone_number,
            body=message
        )

        return sms


twilio_service = TwilioService()