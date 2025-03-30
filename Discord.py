import requests
import json
import re


# get Ziptrader plays -- Date format: YYYY-MM-DD
def get_briefing(date):
    print ("running get_briefing for date: ", date)

    channel_id = "634554429689036830"  # ZT discord channel ID

    # Authorization
    headers = {
        'authorization': 'Nzg5MjUwODgyNzg1MTE2MjAw.GFphV0.43MS6ul4zEDlBGJ-iz-3CfouHjB5r6RcliF_Mo'
    }

    try:
        resp = requests.get(f"https://discord.com/api/v8/channels/{channel_id}/messages", headers=headers)
        # print("get_briefing status code:", resp.status_code)
    except Exception as e:
        print("ERROR: get_briefing - unable to connect to Discord!")
        print(f"Exception is: {e}")

    # load response as json
    jsonn = json.loads(resp.content)
    # print("jsonn", jsonn)

    # find all today's jsons from resp
    today = []
    for value in jsonn:

        if date in value['timestamp']:
            today.append(value)
    formatted_today = json.dumps(today, indent=4)
    # print("formatted_today:", formatted_today)
    
    # patterns to check for plays
    alarm_pattern = r'🚨(.*?):'
    green_pattern = r'✅(.*?):'

    #  find json
    for briefing in today:
        if "🚨" in briefing['content'] \
            or "✅" in briefing['content']:
            alarm_plays= re.findall(alarm_pattern, briefing['content'])
            alarm_plays=[play for play in alarm_plays if " " not in play]

            green_plays= re.findall(green_pattern, briefing['content'])
            green_plays=[play for play in green_plays if " " not in play]

    print("Alarm plays: ", alarm_plays)
    print("Green plays: ", green_plays)
           

    return alarm_plays, green_plays


# run a test
if __name__ == "__main__":

    # Set the desired date for testing
    year=input("year: ")
    day=input("day: ")
    month=input("month: ")
    str_date = f"{year}-{month}-{day}"  #YYYY-MM-DD

    # Call the get_briefing function with the test date
    alarm_plays, green_plays = get_briefing(str_date)

    if alarm_plays == [] and green_plays == []:
        print("No briefing available for the given date.")

   
