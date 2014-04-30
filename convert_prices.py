#! /usr/bin/env python
"""Converts a Google Doc CSV into JSON."""
import csv
import json
import sys
from slugify import slugify

if not len(sys.argv) == 2:
    raise Exception('Usage: python convert_prices.py prices.csv')

records = []
with open(sys.argv[1], 'rb') as csvfile:
    reader = csv.reader(csvfile)
    labels = []
    for index, row in enumerate(reader):
        # The first row is labels which will be used in the json.
        if index == 0:
            labels = [slugify(label) for label in row]
        # The second row is just totals and should be ignored.
        elif index == 1:
            pass
        # Otherwise this contains an actual wine sale.
        else:
            record = {}
            for column, value in enumerate(row):
                record[labels[column]] = value
            records.append(record)

print json.dumps(records, indent=4)