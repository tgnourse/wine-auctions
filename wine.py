#! /usr/bin/env python
from decimal import Decimal
import json
import sys
import re

# The sales tax charged when buying the wine at auction.
SALES_TAX_RATE = 0.09
# The commission charged when selling the wine after the auction.
SALE_COMMISSION = 0.15
# The target profit for any wine purchased at auction.
TARGET_PROFIT = 0.1


def format_cents(cents):
    return '$%.2f' % (float(cents) / 100)

if not len(sys.argv) == 3:
    raise Exception('Usage: python wine.py auctions.json sales.json')

auctions = json.load(open(sys.argv[1]))
sales = json.load(open(sys.argv[2]))

biddable_auctions = []
for auction in auctions:
    matched_sales = []
    # Get the list of matching sales.
    for sale in sales:
        if (auction.get('vintage') == int(sale['year']) and
                sale['winery'] in auction['title'] and
                sale['grape'] in auction['title'] and
                sale['name'] in auction['title'] and
                auction['size'] == 750):
            matched_sales.append(sale)
    # If there were matching sales, we can determine if bidding on the auction would be a good idea.
    if len(matched_sales) > 0:
        # Price per bottle at the current auction price.
        current_price_per_bottle = auction['current_bid'] / auction['quantity']
        auction['current_price_per_bottle'] = current_price_per_bottle

        # Market price per bottle for each sale.
        sale_prices = [int(Decimal(re.sub(r'[^\d.]', '', sale['sold'])) * 100) for sale in matched_sales]
        auction['sale_prices'] = sale_prices
        # print '\tSale prices: %s' % sale_prices
        max_sale_price_per_bottle = max(sale_prices)
        auction['max_sale_price_per_bottle'] = max_sale_price_per_bottle

        # Break even bid is based on the maximum sale price.
        revenue_per_bottle = max_sale_price_per_bottle * (1 - SALE_COMMISSION)
        auction['revenue_per_bottle'] = revenue_per_bottle
        profitable_price_per_bottle = revenue_per_bottle / (1 + TARGET_PROFIT)
        auction['profitable_price_per_bottle'] = profitable_price_per_bottle
        max_bid_per_bottle = profitable_price_per_bottle / (1 + SALES_TAX_RATE)
        auction['max_bid_per_bottle'] = max_bid_per_bottle
        auction['max_bid'] = max_bid_per_bottle * auction['quantity']

        if max_bid_per_bottle > current_price_per_bottle:
            min_profit = (revenue_per_bottle - profitable_price_per_bottle) * auction['quantity']
            auction['min_profit'] = min_profit
            max_profit = (revenue_per_bottle - current_price_per_bottle * (1 + SALES_TAX_RATE)) * auction['quantity']
            auction['max_profit'] = max_profit
            # If there's a potential for sufficient profit, add this to the list of biddable auctions.
            biddable_auctions.append(auction)

print json.dumps(biddable_auctions, indent=4, sort_keys=True)
