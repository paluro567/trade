import os
os.system("echo 'hello world'")


phrase= ' buying 32 shares of Palantir stock at a price of 400 dollars per share'
start="testing phrase around"
end="after text"
combined = start +"'"+phrase+"'"+ end
say= "say"+combined
# print(say)
os.system(f"say  --rate 100 {phrase}")
