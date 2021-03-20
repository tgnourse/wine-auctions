#! /usr/bin/env python
"""Converts a list of auctions from HTML to JSON."""
from HTMLParser import HTMLParser
from decimal import Decimal
import json
import sys
import re
from dateutil.parser import parse


class AuctionHTMLParser(HTMLParser):

    RECORD = 'tf-product clearfix'

    # <div class="tf-pill">RP: 98</div>
    SECTION_RATING = 'tf-pill'

    # <span class="global-pop-color" style=font-weight:bold>$351.00</span>
    SECTION_PRICE = 'global-pop-color'

    # <div class="tf-items">2012 Alban "Lorraine" Edna Valley Syrah (qty: 3)</div>
    SECTION_ITEMS = 'tf-items'

    # <strong class="tf-auction-end-time past-due">End Date: Mar 17 2021 11:00AM PT</strong>
    SECTION_DATE = 'tf-auction-end-time past-due'

    # <div class="tf-product-description">Bid on this 3-bottle lot of 2012 ... </div>
    SECTION_DESCRIPTION = 'tf-product-description'

    # data-app-insights-track-search-click=AuctionItemClick
    HREF_IMAGE = 'AuctionItemClick'

    def __init__(self):
        # Can't call super() because this derives from an old style class.
        # super(AuctionHTMLParser, self).__init__()
        self.reset()
        self.records = []
        self.current_record = None
        self.current_section = None
        self.current_tag = None
        self.current_rating_section = None
        self.current_rater = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        # Put us into various sections.
        if tag == 'div':
            if attrs_dict.get('class') == self.RECORD:
                # Now we're in the record so create a new one.
                self.current_record = {'ratings': {}}
                self.records.append(self.current_record)
            elif attrs_dict.get('class') in [self.SECTION_RATING, self.SECTION_ITEMS, self.SECTION_DESCRIPTION]:
                # We've entered one of the data sections in the record.
                self.current_section = attrs_dict.get('class')
        elif tag == 'span' and attrs_dict.get('class') in [self.SECTION_PRICE]:
            self.current_section = attrs_dict.get('class')
        elif tag == 'strong' and attrs_dict.get('class') in [self.SECTION_DATE]:
            self.current_section = attrs_dict.get('class')
        elif tag == 'a' and attrs_dict.get('data-app-insights-track-search-click') in [self.HREF_IMAGE]:
            self.current_record['sku'] = attrs_dict.get('data-app-insights-track-search-doc-id')
            if attrs_dict.get('href'):
                self.current_record['link'] = 'https://www.klwines.com/' + attrs_dict.get('href').split('&')[0]
            if attrs_dict.get('title'):
                self.current_record['title'] = attrs_dict.get('title').strip()

    def handle_data(self, data):
        data = data.strip()

        if self.current_section == self.SECTION_RATING:
            match = re.search(r'([\w\d]+): ([\w\d]+)', data)
            if match:
                self.current_record['ratings'][match.group(1)] = match.group(2)

        if self.current_section == self.SECTION_ITEMS:
            self.parse_title(data)
            match = re.search(r'qty: ([\d]+)', data)
            if match:
                self.current_record['quantity'] = int(match.group(1))

        if self.current_section == self.SECTION_DATE:
            match = re.search(r'End Date: ([\w\d: ]+)', data)
            if match:
                self.current_record['end_date'] = parse(match.group(1))

        if self.current_section == self.SECTION_PRICE:
            self.current_record['current_bid'] = int(Decimal(re.sub(r'[^\d.]', '', data)) * 100)

        if self.current_section == self.SECTION_DESCRIPTION:
            self.current_record['description'] = self.current_record.get('description', '') + data

    def handle_endtag(self, tag):
        self.current_tag = None
        self.current_section = None

    def parse_title(self, title):
        # Save the full title.
        self.current_record['title_quantity'] = title

        # Pull out the name.
        name_match = re.search(r'([\d-]*)(.*)(\(.*\))', title)
        if name_match:
            self.current_record['name'] = name_match.group(2).strip()

        # Separate the vintage.
        vintage_match = re.search(r'(\d\d\d\d)', title)
        if vintage_match:
            self.current_record['vintage'] = int(vintage_match.group(1))

        # Some vintage matches are verticals.
        vintage_match = re.search(r'(\d\d\d\d-\d\d\d\d)', title)
        if vintage_match:
            self.current_record['vintages'] = vintage_match.group(1)

        # Pull out the size if it's listed. Otherwise we assume it's 750ml.
        ml_match = re.search(r'\((\d*?)ml\)', title)
        l_match = re.search(r'\(([\d\.]*?)L\)', title)
        if ml_match:
            self.current_record['size'] = int(ml_match.group(1))
        elif l_match:
            self.current_record['size'] = int(Decimal(re.sub(r'[^\d.]', '', l_match.group(1))) * 1000)
        else:
            self.current_record['size'] = 750

    @staticmethod
    def date_handler(obj):
        """Augment the JSON handler to handle dates as well."""
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    @property
    def json(self):
        return json.dumps(parser.records, indent=4, default=AuctionHTMLParser.date_handler, sort_keys=True)


html = ''
for line in sys.stdin:
    html += line

parser = AuctionHTMLParser()
parser.feed(html)
print(parser.json)
