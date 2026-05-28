from twilio.rest import Client

from app.config import settings


class TwilioService:
    def __init__(self):
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )

    def start_test_call(self):
        """
        Starts a Twilio outbound call to the test phone number.

        Twilio will call the /twilio/voice/heat-check webhook
        to get TwiML instructions for what to say during the call.
        """

        voice_webhook_url = f"{settings.public_base_url}/twilio/voice/heat-check"
        status_callback_url = f"{settings.public_base_url}/twilio/status"

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