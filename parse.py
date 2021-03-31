from bs4 import BeautifulSoup
import os
import json

dir = 'results'

result = []

for filename in os.listdir(dir):
    with open(os.path.join(dir, filename), 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

        table_rows = soup.find_all(id='MainContent_grdAuctions')[0]

        for tr in table_rows.find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                row.append(td.text.strip())
            if len(row) == 5:
                result.append(row)

file = 'results.json'
with open(file, 'w') as outfile:
    json.dump(result, outfile)
outfile.close()
