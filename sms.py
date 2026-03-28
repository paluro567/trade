import os
import time
import requests
import platform


def text(message):



    resp = requests.post('https://textbelt.com/text', {
        'phone': os.environ.get('SMS_PHONE'),
        'message': message,
        'key': os.environ.get('TEXTBELT_API_KEY'),
    })

    print(resp.json())
    time.sleep(5)

    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


# Example run
if __name__=="__main__":
    text("refactored")
