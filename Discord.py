import requests
import json
import re



def get_briefing(date):
    print ("running get_briefing for date: ", date)

    channel_id = "634554429689036830"  # Zip trader discord channel ID

    # Discord request headers
    headers = {
        'authorization': 'Nzg5MjUwODgyNzg1MTE2MjAw.GFphV0.43MS6ul4zEDlBGJ-iz-3CfouHjB5r6RcliF_Mo'
    }
    try:
        resp = requests.get(f"https://discord.com/api/v8/channels/{channel_id}/messages", headers=headers)
        print("request status code:", resp.status_code)
    except Exception as e:
        print("ERROR: Unable to connect to Discord!")
        print(f"Exception is: {e}")

    # load response as json
    jsonn = json.loads(resp.content)
    # print("jsonn", jsonn)

    # find all today's jsons from resp
    today = []
    for value in jsonn:
        # print("json in response: ", value, "\n\n")

        if date in value['timestamp']:
            today.append(value)
    formatted_today = json.dumps(today, indent=4)
    print("formatted_today:", formatted_today)


    #  Hashmaps to keep track of tickers with support/resistance values
    supports = {}
    resistances = {}
    retail=[]
    alarm_plays=[]
    alarm_pattern = r'🚨(.*?):'
    green_pattern = r'✅(.*?):'

    for briefing in today:
        if "🚨" in briefing['content'] \
            or "✅" in briefing['content']:     
            alarm_plays= re.findall(alarm_pattern, briefing['content'])
            alarm_plays=[play for play in alarm_plays if " " not in play ]

            green_plays= re.findall(green_pattern, briefing['content'])
            green_plays=[play for play in green_plays if " " not in play ]

    print("new alarm_plays: ", alarm_plays)
    print("new green_plays: ", green_plays)
           

    return alarm_plays, green_plays
def getnum(original):
    num_dot = 0  # keeps track of number of '.'
    num = ""
    for c in original:
        if c == '.':
            num_dot += 1
        if num_dot > 1:
            break
        if not c.isnumeric() and c != ".":
            break
        num += c
    return float(num)


# run a test
if __name__ == "__main__":
    # Set the desired date for testing
    day=input("day: ")
    test_date = f"2024-03-{day}"

    # Call the get_briefing function with the test date
    alarm_plays, green_plays = get_briefing(test_date)

    if alarm_plays == [] and green_plays == []:
        print("No briefing available for the given date.")

   
