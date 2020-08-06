import json
from datetime import datetime
import requests
import base64
from bs4 import BeautifulSoup


class StockXAPI:
    def __init__(self, username=None, password=None):
        self.username = ''
        self.password = ''
        self.client_id = ''
        self.token = ''

        if username and password:
            self.login(username, password)

    def _process_json(self, json_data, output_data):
        # Split output data categories into first and second layers
        return_data = [i for i in output_data if type(i) == str]
        secondary_return_data = [i for i in output_data if type(i) == list]

        product_data = {}

        # Add categories from output_data that are in the json to product_data
        for key in return_data:
            if key in json_data:
                product_data[key] = json_data[key]

        for top_key, bottom_key in secondary_return_data:
            for key in json_data[top_key]:
                if key == bottom_key:
                    product_data[bottom_key] = json_data[top_key][bottom_key]

        return product_data

    def _get_login_info(self):
        url = 'https://stockx.com/login'

        user_agent = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36'
                                    ' (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

        resp = requests.get(url, headers=user_agent)

        # Get the value of the csrf cookie.
        cookie_headers = resp.headers['Set-Cookie']
        cookie_csrf_end = cookie_headers.find(';') + 1
        cookie_csrf = cookie_headers[:cookie_csrf_end]

        # Get the base 64 string from the html that contains necessary information.
        soup = BeautifulSoup(resp.content, 'html.parser')
        script_content = str(soup.body.find_all('script')[5])

        config_start = script_content.find('window.atob') + 13
        config_end = script_content.find("'))));")
        config_data = script_content[config_start:config_end]

        # Get the csrf and the client id.
        output = json.loads(base64.b64decode(config_data))
        client_id = output['clientID']
        data_csrf = output['internalOptions']['_csrf']

        self.client_id = client_id
        return cookie_csrf, data_csrf

    def login(self, username, password):
        login_url = 'https://accounts.stockx.com/usernamepassword/login'

        cookie_csrf, data_csrf = self._get_login_info()

        login_headers = {'content-type': 'application/json',
                         'cookie': cookie_csrf,
                         'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2)'
                                       ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

        login_data = {'client_id': self.client_id,
                      'tenant': 'stockx-prod',
                      '_csrf': data_csrf,
                      'username': username,
                      'password': password,
                      'connection': 'production'}
        
        resp = requests.post(login_url, headers=login_headers, json=login_data)
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Try to get the authentication token from the returned html.
        try:
            token = soup.find('input', {'name': 'wresult'})['value']
        except TypeError:
            print('Incorrect username or password')
            return None

        self.username = username
        self.password = password

        self.token = token

    def search_items(self, search_term, output_data, page=1, max_searches=-1):
        search_term = search_term.replace(' ', '%20')
        url = 'https://stockx.com/api/browse?&page={}&_search={}&dataType=product&country=US'.format(page, search_term)

        user_agent = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36'
                                    ' (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

        # Get the product list and add each product to final_data.
        resp = requests.get(url, headers=user_agent)
        data = json.loads(resp.content)['Products'][:max_searches]

        final_data = []
        for item in data:
            final_data.append(self._process_json(item, output_data))

        return final_data

    def get_item_data(self, item_id, output_data):
        url = 'https://stockx.com/api/products/{}'.format(item_id)

        user_agent = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36'
                                    ' (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}
        # Get the product data for the item.
        resp = requests.get(url, headers=user_agent)
        data = json.loads(resp.content)['Product']

        # Get the market data for the item.
        market_data_url = 'https://stockx.com/api/products/{}/market'.format(item_id)
        resp = requests.get(market_data_url, headers=user_agent)
        market_data = json.loads(resp.content)['Market']

        data['market'] = market_data
        final_data = self._process_json(data, output_data)
        return final_data

    def get_past_prices(self, item_id, start_date='all', end_date=None, data_points=100):
        url = 'https://stockx.com/api/products/{}/chart?start_date={}&end_date={}' \
              '&intervals={}&format=highstock&currency=USD&country=US'.format(item_id, start_date, end_date,
                                                                              data_points)

        user_agent = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36'
                                    ' (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

        resp = requests.get(url, headers=user_agent)
        data = json.loads(resp.content)['series'][0]['data']

        x = []
        y = []

        # Append date and price to x and y
        for timestamp, price in data:
            x.append(datetime.fromtimestamp(int(timestamp / 1000)))
            y.append(price)

        return x, y
