'''scheduled scripts:
0 17 * * * /path/to/stop_script.sh

30 9 * * 1-5 /home/peter_luro1/miniconda3/envs/tradeenv/bin/python /home/peter_luro1/trade/test-12-10.py >> /home/peter_luro1/>
30 9 * * 1-5 /home/peter_luro1/miniconda3/envs/tradeenv/bin/python /home/peter_luro1/trade/test-12-16.py >> /home/peter_luro1/>
'''
#!/bin/bash

pkill -f "/home/peter_luro1/miniconda3/envs/tradeenv/bin/python /home/peter_luro1/trade/test-12-10.py"
pkill -f "/home/peter_luro1/miniconda3/envs/tradeenv/bin/python /home/peter_luro1/trade/test-12-16.py"
pkill -f "/home/peter_luro1/miniconda3/envs/tradeenv/bin/python /home/peter_luro1/trade/realtime.py"


