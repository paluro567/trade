import requests
from bs4 import BeautifulSoup

headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
stock='PLTR'
url=f'https://finance.yahoo.com/quote/{stock}/'
r = requests.get(url)


soup= BeautifulSoup(r.text, 'html.parser')
print("status: ",r.status_code)

price=soup.find('div', {'class':"D(ib) Mend(20px)"})
print("price: ", price)

print("price text: ", price.text)