from twilio.rest import Client
from secret import *

bold='\33[1m'
def twilio_text(message):
    cl = Client(SID, auth_token)
    cl.messages.create(body=message, from_= twilio_number, to= cell_phone)
    print("Successful text message sent: ", message)


twilio_text('*4PM* not bold')