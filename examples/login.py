from stockx import StockXAPI

username = ''
password = ''

s = StockXAPI()
s.login(username, password)
print(s.token)
