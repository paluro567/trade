import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


def scrape_stock_price(stock):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    url = f'https://finance.yahoo.com/quote/{stock}/'
    r = requests.get(url, headers=headers)

    soup = BeautifulSoup(r.text, 'html.parser')

    price = soup.find(class_="quote-header-section Cf Bxz(cb) Pos(r) Mb(5px) Bgc($lv2BgColor) Maw($maxModuleWidth) Miw($minGridWidth) smartphone_Miw(ini) Miw(ini)!--tab768 Miw(ini)!--tab1024 Mstart(a) Mend(a) Px(20px) smartphone_Pb(0px) smartphone_Mb(0px) smartphone_Z(11)")

    resp_price_string = price.text.split("trend2W10W9M")[1]
    string_price = ""
    for char in resp_price_string:
        if char.isdigit() or char == ".":
            string_price += char
        else:
            break

    return float(string_price)



if __name__ == '__main__':
 
    # Call the function to get the stock price and store it in the DataFrame
    p = scrape_stock_price('pltr')

    # Print the DataFrame
    print(p)
