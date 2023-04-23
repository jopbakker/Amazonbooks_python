#!/usr/bin/env python3

from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import csv
import json
import logging
import lxml
import random
import re
import requests
import sys

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--author",
                    dest="check_author",
                    help="Custom author check - [Default: all]",
                    default='all',
                    action='store')
parser.add_argument("-aL", "--author-list",
                    dest="author_list",
                    help="Custom filename for the csv file containing authors and urls - [Default: authors.csv]",
                    default='authors.csv',
                    action='store')
parser.add_argument("--author-file-folder",
                    dest="author_files_folder",
                    help="Custom authors file location - [Default: authors]",
                    default='authors',
                    action='store')
parser.add_argument("--log-level",
                    dest="log_level",
                    help="Set the level of logs to show (Options: DEBUG, INFO, WARNING, ERROR, CRITICAL) - [Default: WARNING]",
                    default='INFO',
                    action='store')
parser.add_argument("--test",
                    dest="test_run",
                    help="Set this to 'True' to run the script without sending the pushover message or saving the author files",
                    default=False,
                    action='store')
parser.add_argument("-Pu", "--pushover-user-token",
                    dest="user_token",
                    help="Pushover user token",
                    action='store')
parser.add_argument("-Pa", "--pushover-api-token",
                    dest="api_token",
                    help="Pushover API token",
                    action='store')

args = parser.parse_args()

if not args.test_run and not args.user_token and not args.api_token:
    parser.error("-Pu (--pushover-user-token) and -Pa (--pushover-api-token) are required when not doing a test run.")


logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=args.log_level.upper())

def read_input_csv(author_list):
    logging.info(f"Parsing the data from the author-list file: {author_list}")
    with open(author_list, 'r') as file:
        reader = csv.DictReader(file)
        author_list = []
        for index, row in enumerate(reader):
            author_list.append(row)
            author_list[index]['url'] = "https://www.amazon.com/s?k=\"{}\"&i=digital-text&s=date-desc-rank".format(row['author'].replace(" ","+"))
    
    return author_list

def download_user_agent_list():
    ua_raw_url = "https://gist.githubusercontent.com/pzb/b4b6f57144aea7827ae4/raw/cf847b76a142955b1410c8bcef3aabe221a63db1/user-agents.txt"

    headers = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0 SeaMonkey/2.35',
            'Accept-Language': 'en-US, en;q=0.5'})
    raw_html = requests.get(ua_raw_url, headers=headers).text
    user_agent_list = list(raw_html.split("\n"))
    random.shuffle(user_agent_list)

    return user_agent_list


def test_amazon_request(user_agent_list):
    test_url = 'https://www.amazon.com/s?k="Robin+Hobb"&i=digital-text&s=date-desc-rank'
    

    for user_agent in user_agent_list:
        headers = ({'User-Agent':
                f'{user_agent}',
                'Accept-Language': 'en-US, en;q=0.5'})
        raw_html = requests.get(test_url, headers=headers).text
        bad_ua = re.search('To discuss automated access to Amazon data please contact api-services-support@amazon.com.',str(raw_html))

        if bad_ua:
            logging.debug("Fail on user agent: {}".format(user_agent))
        else:
            logging.info("Success on user agent string: {}".format(user_agent))
            return headers

def download_html(author,author_url, headers):
    logging.info("Start looking for need books for author: {}".format(author))
    logging.debug(f"Downloading the HTML code from {author_url}")
    raw_html = requests.get(author_url, headers=headers).text
    
    return raw_html

def parse_html(author, author_html):
    books = []

    soup = BeautifulSoup(author_html, 'lxml')
    books_div = soup.find_all('div', {"class": "sg-col sg-col-4-of-12 sg-col-8-of-16 sg-col-12-of-20 sg-col-12-of-24 s-list-col-right"})
    images_div = soup.find_all('div', {"class": "sg-col sg-col-4-of-12 sg-col-4-of-16 sg-col-4-of-20 sg-col-4-of-24 s-list-col-left"})

    for index, book_div in enumerate(books_div):
        try:
            book_data_raw = book_div.find_all(string=True)
            image_data_raw = images_div[index]
            contains_author = re.search(author,str(book_data_raw))
            contains_audiobook = re.search('Audible Audiobook',str(book_data_raw))

            date_pattern = r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
            contains_date = re.search(date_pattern, str(book_data_raw))
            contains_now_date = re.search("Available instantly",str(book_data_raw))

            series_pattern = r"Book (\d{1,3} of \d{1,3}): (.+?)\'\,"
            contains_series = re.search(series_pattern, str(book_data_raw))

            cover_pattern = r"src\=\"(.+?)\" srcset"
            cover_link = re.search(cover_pattern, str(image_data_raw))
            cover_render_pattern = r"(W\/IMAGE.+images\/)"

            if contains_author and (contains_now_date or contains_date) and not contains_audiobook:
                    data = {}
                    data['author'] = author
                    data['title'] = book_data_raw[0]
                    if contains_series:
                        data['series'] = contains_series.group(2)
                        data['bookInSeries'] = contains_series.group(1)
                    else:
                        data['series'] = ""
                        data['bookInSeries'] = ""
                    if cover_link:
                        cover_url = cover_link.group(1)
                        if cover_render_pattern:
                            cover_url = re.sub(cover_render_pattern,'',cover_link.group(1))
                        data['coverUrl'] = cover_url
                    else:
                        data['coverUrl'] = ""
                    if contains_now_date:
                        data['releaseDate'] = "Available instantly"
                    elif contains_date:
                        data['releaseDate'] = contains_date.group(0)
                    else:
                        data['releaseDate'] = ""

                    books.append(data)
        except:
            continue
    return books

def read_author_file(author_file_location):
    try:
        with open(author_file_location, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}
    return data

def compare_books(author, new_books, known_books):
    new_or_updated_books = []

    # iterate over each book in new_books
    for book in new_books:
        # create a new dictionary that only contains the relevant keys for comparison
        new_book = {k: v for k, v in book.items() if k != 'lastUpdate'}
        
        # iterate over each book in known_books and create a new dictionary that only contains the relevant keys for comparison
        known_books_titles_and_series = []
        for known_book in known_books:
            known_book_titles_and_series = {k: v for k, v in known_book.items() if k != 'lastUpdate'}
            known_books_titles_and_series.append(known_book_titles_and_series)
        
        # check if the new_book is in known_books_titles_and_series
        if new_book not in known_books_titles_and_series:
            book['lastUpdate'] = datetime.today().strftime('%Y-%m-%d')
            new_or_updated_books.append(book)
        
    if new_or_updated_books:
        message = []
        for book in new_or_updated_books:
            book = book['title'] + " - " + book['releaseDate']
            message.append(book)
        message = " \n".join(message)
        logging.info("Found new or updated books for author: {} \nBooks: {}\n".format(author, message))
    else:
        logging.info("No new books or updates found for author: {}".format(author))
    
    return new_or_updated_books

def update_author_file(author_file_location, new_or_updated_books, known_books):
    # create a new list that contains all known books and all new or updated books
    known_books_dict = {book['title']: book for book in known_books}

    # Loop over the new or updated books and update the known books dict accordingly
    for book in new_or_updated_books:
        # If the book already exists in the known_books_dict, update its values
        if book['title'] in known_books_dict:
            known_books_dict[book['title']].update(book)
        # Otherwise, add the book to the known_books_dict
        else:
            known_books_dict[book['title']] = book

    # Convert the known_books_dict back to a list of books and sort by title
    all_books = sorted(list(known_books_dict.values()), key=lambda x: x['title'])


    with open(author_file_location, 'w+', encoding='utf-8') as f:
        json.dump(all_books, f, ensure_ascii=False, indent=4)

def send_pushover_message(author, new_or_updated_books, user_token, api_token):
    message = []
    for book in new_or_updated_books:
        book = book['title'] + " - " + book['releaseDate']
        message.append(book)
    message = " \n".join(message)

    payload = {"title": author, "message": message, "user": user_token, "token": api_token }
    logging.debug(payload)
    try:
        logging.info("Sending pushover message")
        requests.post('https://api.pushover.net/1/messages.json', data=payload, headers={'User-Agent': 'Python'})
    except Exception as e:
        logging.error("Sening pushover message failed with error: {}".format(e))



def check_author(author,author_url,author_file_location,user_agent_list,user_token, api_token):
    
    header = test_amazon_request(user_agent_list)
    author_html = download_html(author,author_url,header) # get raw html from author recent book page -- output: raw html
    new_books = parse_html(author,author_html) # get current books -- output: dict with current book data
    known_books = read_author_file(author_file_location) # get existing book -- output: dict with known books
    new_or_updated_books = compare_books(author, new_books, known_books) # compare new and known books -- output: dict of new or updates books
    if not args.test_run:
        if new_or_updated_books: # update author file with new books -- output author file with all books and up-to-date release date
            update_author_file(author_file_location, new_or_updated_books, known_books)
            send_pushover_message(author, new_or_updated_books, user_token, api_token)

def main():
    logging.info("Executing the script with the following arguments: {}".format(sys.argv[1:]))
    author = args.check_author
    author_files_folder = args.author_files_folder
    author_list = read_input_csv(args.author_list)

    user_agent_list=download_user_agent_list()

    if author == "all":
        for row in author_list:
            author = row["author"]
            author_url = row["url"]
            author_file_location = "{}/{}.json".format(author_files_folder,author.replace(" ","_"))
            check_author(author,author_url,author_file_location,user_agent_list,args.user_token,args.api_token)
    else:
        for row in author_list:
            found_author = False
            if row["author"] == author:
                found_author = True
                author_url = row["url"]
                author_file_location = "{}/{}.json".format(author_files_folder,author.replace(" ","_"))
                check_author(author,author_url,author_file_location,user_agent_list,args.user_token,args.api_token)
                break
        if not found_author:
            logging.error("Author {} not found in author list.".format(author))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt Detected.")
        print("Exiting...")
        exit(0)