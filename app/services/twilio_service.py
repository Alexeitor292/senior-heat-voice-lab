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
        Step 3 call.

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


twilio_service = TwilioService()