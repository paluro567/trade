import requests
import json


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

    # find all today's jsons from resp
    today = []
    for value in jsonn:
        # print("json in response: ", value, "\n\n")

        if date in value['timestamp']:
            today.append(value)
    formatted_today = json.dumps(today, indent=4)
    # print(f"\n\ntoday({len(today)}): ", formatted_today)

    with open("todays-briefings.txt", "w") as outfile:
        outfile.write(formatted_today)

    #  Hashmaps to keep track of tickers with support/resistance values
    supports = {}
    resistances = {}
    retail=[]
    alarm_plays=[]

    for briefing in today:
        if "Most talked about stocks on retail forums include" in briefing['content']:
            retail = briefing['content'].split("retail forums include")[1]
            retail = retail.split(",")
            print("retail plays: ", retail)
            last = ""
            last_index = 0
            last_set=False
            # get retail plays
            for i in range(0, len(retail)):
                if "Briefings" in retail[i] and not last_set:
                    last_index = i
                    print(f"retail[{i}]: ", retail[i])
                    for c in retail[i]:
                        if c != '\n':
                            last += c
                        else:  # new line character is found
                            last_set = True
                            last = last.split(' ')[-1]  # remove the and from the last ticker in the retail list
                            break
            retail = retail[0:last_index]
            if last!='':
                retail.append(last)
            i = 0
            for play in retail:
                retail[i] = play.strip()
                i += 1

        if "@" in briefing['content'] and ":" in briefing['content']:
            print("Catalyst Plays: \n\n", briefing['content'], "\n-----------------------Today's Data-----------------------\n")
            content = briefing['content']
            print(briefing)

            check_mark = chr(9989)
            split_one = content.split(check_mark)
            print("content is:", content)
            split_colon = content.split(':')
            print("split colon:", split_colon)

            # get alarm plays
            alarm_plays = []
            for spl in split_colon:
                if '🚨' in spl:
                    alarm_play=spl.split('🚨')[-1]
                    alarm_plays.append(alarm_play.strip(' '))
                else:
                    continue
            print("alarm plays: ", alarm_plays)
            

            # get supports and resistances
            for split_res in split_one:
                if ":" in split_res and '@' in split_res:
                    ticker = str(split_res.split(":")[0]).strip(' ')
                    print("ticker: ", ticker)
                    # Current Support Value
                    try:
                        cur_support = split_res.split(":")[1].split("support @")[1]
                        support = getnum(cur_support)
                    except:
                        support=0

                    print("support: ", support)
                    supports[ticker] = support
                    # current resistance Value
                    try:
                        cur_res = split_res.split("resistance @")[1]
                        resistance = getnum(cur_res)
                    except:
                        resistance=0
                    print("resistance: ", resistance)
                    resistances[ticker] = resistance
            
            print("supports:", supports)
            print("resistances:", resistances)

            # print(f"plays: {list(supports.keys())}", "\nresistances: ", resistances, "\nsupports: ", supports)
    try:
        return resistances, supports, retail, alarm_plays if alarm_plays else []
    except Exception as e:
        print("NO BRIEFING YET!")
        print(f"Exception is: {e}")


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
    from datetime import datetime
    import datetime

    curr_date  =  datetime.datetime.now().strftime('%Y-%m-%d')
    print("curr_date: ", curr_date)
    resistances, supports, retail, alarm_plays = get_briefing(curr_date)
    alarm_plays = [stock for stock in alarm_plays if ' ' not in stock]
    green_plays = list(supports.keys())
    other_on_radar = ['SLNH','PLTR','AI', 'SFWL']

    print("today's alarm_plays: ", alarm_plays )
    print("today's retail: ", retail)
    print("today's green_plays: ", green_plays)
    if alarm_plays == [] and green_plays == []:
        print("exception made...")
   
