from stockx import StockXAPI
import matplotlib.pyplot as plt
from datetime import date

stockx = StockXAPI()

# Search 'supreme' and get the name, id, and last sale price from 5.
search_term = 'supreme'
products = stockx.search_items(search_term=search_term, output_data=['name', 'id', ['market', 'lastSale']],
                               page=1, max_searches=5)
for product in products:
    print(product)

# Get the name, last sale price, and lowest ask from this id.
item_id = '79cdebf9-a1c1-4eb0-b46a-c5adeebdaaf9'
item_info = stockx.get_item_data(item_id=item_id, output_data=['name', ['market', 'lastSale'],
                                                               ['market', 'lowestAsk'], ['market', 'highestBid']])
print('\n', item_info)

# Plot a graph of past sale prices for this id
item_id = '79cdebf9-a1c1-4eb0-b46a-c5adeebdaaf9'
current_date = date.today()
x, y = stockx.get_past_prices(item_id=item_id, start_date='all', end_date=current_date, data_points=20)

plt.plot(x, y)
plt.gcf().autofmt_xdate()
plt.show()

