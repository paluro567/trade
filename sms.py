import os
import time
import requests
import platform


def text(message):



    resp = requests.post('https://textbelt.com/text', {
        'phone': '9786219450',
        'message': message,
        'key': 'ab8202f42c7b7aae633e8a80b56e1d58b98456d3Y9ohGTmXAqSRAIeH6levq0F47',
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
