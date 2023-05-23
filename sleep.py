from datetime import datetime
from datetime import date
import pause
from datetime import datetime
import time

# Sleep until 9:00am
run_hour = 9
run_minute = 00

# get today's month day and year
now = datetime.now()
month = now.strftime("%m")
day = now.strftime("%d")
year = now.strftime("%Y")

print("\n\nSleeping until 9:00am today")
pause.until(datetime(int(year), int(month), int(day), run_hour, run_minute, 0))
print("running now!")




