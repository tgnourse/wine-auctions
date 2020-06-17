#! /usr/bin/env python
"""Converts a list of auctions from HTML to JSON."""
from HTMLParser import HTMLParser
from decimal import Decimal
import json
import sys
import re
from dateutil.parser import parse


class AuctionHTMLParser(HTMLParser):

    RECORD = 'result clearfix'

    SECTION_IMAGE = 'auctionProductImg'
    SECTION_DESCRIPTION = 'auctionResult-desc'
    SECTION_INFO = 'result-info'
    SECTION_RATING = 'rating'

    RATING_RATING = 'rating global-serif'
    RATING_RATER = 'rater'

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
            elif attrs_dict.get('class') in [self.SECTION_IMAGE, self.SECTION_DESCRIPTION, self.SECTION_INFO]:
                # We've entered one of the data sections in the record.
                self.current_section = attrs_dict.get('class')

        if tag == 'span':
            if attrs_dict.get('class') == self.SECTION_RATING:
                self.current_section = self.SECTION_RATING

        # Do section specific parsing.
        if self.current_section == self.SECTION_DESCRIPTION:
            if tag == 'a':
                self.parse_title(attrs_dict.get('title'))
                self.current_record['link'] = attrs_dict.get('href')
                sku_match = re.search(r'sku=(\d+)', attrs_dict.get('href'))
                if sku_match:
                    self.current_record['sku'] = int(sku_match.group(1))

        if self.current_section == self.SECTION_RATING:
            if tag == 'span':
                if attrs_dict.get('class') in [self.RATING_RATER, self.RATING_RATING]:
                    self.current_rating_section = attrs_dict.get('class')

    def handle_data(self, data):
        data = data.strip()
        if self.current_section == self.SECTION_DESCRIPTION:
            # Find the quantity in data for this section.
            match = re.search(r'qty: ([\d]+)', data)
            if match:
                self.current_record['quantity'] = int(match.group(1))
                return
            # Find and parse the end date which occurs in this section.
            match = re.search(r'End Date: ([\w\d: ]+)', data)
            if match:
                self.current_record['end_date'] = parse(match.group(1))

        if self.current_section == self.SECTION_INFO:
            # Get the current bid price.
            if data != '' and self.current_tag == 'strong':
                self.current_record['current_bid'] = int(Decimal(re.sub(r'[^\d.]', '', data)) * 100)

        if self.current_section == self.SECTION_RATING:
            if self.current_rating_section == self.RATING_RATER:
                self.current_rater = data
                self.current_rating_section = None
            if self.current_rating_section == self.RATING_RATING and self.current_rater:
                self.current_record['ratings'][self.current_rater] = data
                self.current_rating_section = None
                self.current_rater = None

    def handle_endtag(self, tag):
        self.current_tag = None

    def parse_title(self, title):
        # Save the full title.
        self.current_record['title'] = title

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
