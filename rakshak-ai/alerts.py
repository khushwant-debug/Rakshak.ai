import os

# BASE_DIR for safe path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Alerts:
    def __init__(self):
        self.twilio_sid = os.getenv('TWILIO_SID')
        self.twilio_token = os.getenv('TWILIO_TOKEN')
        self.twilio_from = os.getenv('TWILIO_FROM')
        self.twilio_to = os.getenv('TWILIO_TO')

    def send_sms(self):
        if not all([self.twilio_sid, self.twilio_token, self.twilio_from, self.twilio_to]):
            print("Twilio credentials not set, skipping SMS")
            return
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            message = client.messages.create(
                body="Accident detected by Rakshak AI!",
                from_=self.twilio_from,
                to=self.twilio_to
            )
            print(f"SMS sent: {message.sid}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")

    def play_siren(self):
        # In cloud environments, playing audio is not available. Guard and fail safely.
        # Set DISABLE_SIREN=1 in environment to explicitly disable siren playback.
        if os.environ.get('DISABLE_SIREN', '1') == '1':
            print("Siren disabled by environment; skipping play_siren")
            return

        siren_path = os.path.join(BASE_DIR, 'static', 'siren 2.mp3.mp3')
        if not os.path.exists(siren_path):
            print(f"Siren file not found at {siren_path}; skipping playback")
            return

        try:
            # Import locally to avoid requiring audio libs on servers
            from playsound import playsound
            playsound(siren_path)
        except Exception as e:
            print(f"Failed to play siren: {e}")

    def show_alert(self):
        # This would be handled by JavaScript in the frontend
        pass
