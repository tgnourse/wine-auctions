import requests
from bs4 import BeautifulSoup
import datetime

start_date_and_time = datetime.datetime.now()

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.klwines.com",
    "referer": "https://www.klwines.com/Auction/Information/AuctionPastLotsList.aspx",
    "sec-ch-ua": "\"Google Chrome\";v=\"89\", \"Chromium\";v=\"89\", \";Not\\\"A\\\\Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?1",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/89.0.4389.90 Mobile Safari/537.36",
}

body = {
    "ctl00$MainContent$txtLotName": "",
    "ctl00$MainContent$txtRangeBegin": "",
    "ctl00$MainContent$txtRangeEnd": "",
    "ctl00$MainContent$txtPriceRangeBegin": "",
    "ctl00$MainContent$txtPriceRangeEnd": "",
    "ctl00$MainContent$btnSearch.x": "52",
    "ctl00$MainContent$btnSearch.y": "9",
}

body_next = {
    "ctl00$MainContent$txtLotVintagePrefix": "",
    "ctl00$MainContent$txtLotName": "",
    "ctl00$MainContent$txtRangeBegin": "",
    "ctl00$MainContent$txtRangeEnd": "",
    "ctl00$MainContent$txtPriceRangeBegin": "",
    "ctl00$MainContent$txtPriceRangeEnd": "",
    "ctl00$MainContent$Btn_Next": "Next",
}

url = 'https://www.klwines.com/Auction/Information/AuctionPastLotsList.aspx'

def get_asp_vars(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    ids = [
        '__EVENTVALIDATION',
        '__VIEWSTATE',
        '__VIEWSTATEGENERATOR',
        '__EVENTTARGET',
        '__EVENTARGUMENT',
    ]

    result = {}
    for field_id in ids:
        tags = soup.find_all(id=field_id)
        if tags:
            result[field_id] = tags[0]['value']
        else:
            result[field_id] = None

    return result


def get_page_number(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    result = {}
    tags = soup.find_all(id='MainContent_lblCurrentPageNumber')
    if tags:
        result['page'] = tags[0].string

    tags = soup.find_all(id='MainContent_lblTotalPages')
    if tags:
        result['pages'] = tags[0].string

    return result


def output_file(page, pages, start_date_and_time):
    current_date_and_time = datetime.datetime.now()
    current_date_and_time_string = str(current_date_and_time)
    start_date_and_time_string = str(start_date_and_time)
    extension = ".html"

    file_name = "results/" + start_date_and_time_string + " " + page + " of " + pages + " " + current_date_and_time_string + extension
    return open(file_name, 'w')


def save_result(html_doc, start_date_and_time):
    page_info = get_page_number(html_doc)
    f = output_file(page_info.get('page'), page_info.get('pages'), start_date_and_time)
    f.write(html_doc)
    f.close()
    return f.name


# First request that gets the regular page.
response = requests.get(url=url, headers=headers)

# Get the first page of results
response = requests.post(url=url, data={**body, **get_asp_vars(response.text)}, headers=headers)
print(save_result(response.text, start_date_and_time))

# Get every subsequent page of results
while True:
    response = requests.post(url=url, data={**body_next, **get_asp_vars(response.text)}, headers=headers)
    print(save_result(response.text, start_date_and_time))
