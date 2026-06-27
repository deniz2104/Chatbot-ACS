from azure.communication.email import EmailClient
from src.azure.acs.otp import generate_otp, store_otp
from src.azure.kv.get_secrets_from_kv import get_acs_connection_string, get_acs_sender_address

def send_otp_email(username: str, to_email: str, reason: str = "verification") -> None:
    otp = generate_otp()
    sender = get_acs_sender_address()
    client = EmailClient.from_connection_string(get_acs_connection_string())
    store_otp(username, otp)

    message = {
        "senderAddress": sender,
        "recipients": {"to": [{"address": to_email}]},
        "content": {
            "subject": f"Chatbot ACS - {reason.capitalize()} Code",
            "plainText": (
                f"Your {reason} code is: {otp}\n\n"
                "This code expires in 10 minutes. Do not share it with anyone."
            ),
        },
    }
    poller = client.begin_send(message)
    poller.result()
