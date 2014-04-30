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
TARGET_PROFIT = 0.05


def format_cents(cents):
    return '$%.2f' % (float(cents) / 100)

if not len(sys.argv) == 3:
    raise Exception('Usage: python wine.py auctions.json sales.json')

auctions = json.load(open(sys.argv[1]))
sales = json.load(open(sys.argv[2]))

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

        # Market price per bottle for each sale.
        sale_prices = [int(Decimal(re.sub(r'[^\d.]', '', sale['sold'])) * 100) for sale in matched_sales]
        # print '\tSale prices: %s' % sale_prices
        max_sale_price_per_bottle = max(sale_prices)

        # Break even bid is based on the maximum sale price.
        revenue_per_bottle = max_sale_price_per_bottle * (1 - SALE_COMMISSION)
        profitable_price_per_bottle = revenue_per_bottle / (1 + TARGET_PROFIT)
        max_bid_per_bottle = profitable_price_per_bottle / (1 + SALES_TAX_RATE)

        if max_bid_per_bottle > current_price_per_bottle:
            print '%s bottles of [%s] matched %s sold bottles' % (auction['quantity'], auction['title'],
                                                                  len(matched_sales))
            print '\tMax sale price: %s' % format_cents(max_sale_price_per_bottle)
            print '\tRevenue per bottle: %s' % format_cents(revenue_per_bottle)
            print '\tProfitable price per bottle: %s' % format_cents(profitable_price_per_bottle)
            print '\tCurrent bid: %s (%s per bottle)' % (format_cents(auction['current_bid']),
                                                         format_cents(current_price_per_bottle))
            print '\tMy bid: %s (%s per bottle)' % (format_cents(max_bid_per_bottle * auction['quantity']),
                                                    format_cents(max_bid_per_bottle))
            min_profit = (revenue_per_bottle - profitable_price_per_bottle) * auction['quantity']
            print '\tMin profit: %s' % format_cents(min_profit)
            print '\thttp://www.kandl.com%s' % auction['link']
        # else:
        #     print '\tNot Profitable'
