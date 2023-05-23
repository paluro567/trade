
from secret import *
from twilio.rest import Client


def twilio_text(message):
    cl = Client(SID, auth_token)
    cl.messages.create(body=message, from_= twilio_number, to= cell_phone)
    print("Successful text message sent: ", message)