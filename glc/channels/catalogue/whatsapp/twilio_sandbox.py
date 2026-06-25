import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

acc_sid = str(os.getenv("TWILIO_ACCOUNT_SID"))
token = str(os.getenv("TWILIO_AUTH_TOKEN"))

def send_sandbox_message():
    print(f"acc_sid {acc_sid}, token {token[:-4]}")
    if acc_sid is not None or token is not None:
        client = Client(username=acc_sid, password=token)

        message = client.messages.create(
            from_=os.getenv("TWILIO_SANDBOX_NUMBER"),
            to=os.getenv("TWILIO_TEST_TO"),
            body="Twilio sandbox wiring test from .env",
        )

        message = client.messages(message.sid).fetch()
        print("Status:", message.status)
        print("To:", message.to)
        print("From:", message.from_)
        print("Error code:", message.error_code)
        print("Error message:", message.error_message)
        print("After Sandbox Message")


if __name__ == "__main__":
    send_sandbox_message()

