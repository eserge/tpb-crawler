#!/usr/bin/env python

import argparse
import time
from datetime import datetime
import re

from pymongo import MongoClient
from pyquery import PyQuery as pq
import requests

mongo_client = MongoClient()
db = mongo_client.tpbmeta

argument_parser = argparse.ArgumentParser(
    description='Add a URL to DB for later processing.'
)
argument_parser.add_argument(
    'URL', nargs='*', help='A URL to add.'
)


def insert_page(id, short_url, url):
    result = db.pages.insert_one({
        'url': url,
        'short_url': short_url,
        'torrent_id': id,
        'added_at': time.mktime(datetime.utcnow().timetuple()),
    })
    return result


class ParsePagesList(object):
    def __init__(self, db, arguments):
        self.db = db
        self.args = arguments
        self.path_re = re.compile(r'^(\/torrent\/(\d+)\/).*')
        self.inserted_ids = []

    def parse_documents(self):
        downloaded_list_documents = []
        for url in self.args.URL:
            try:
                result = requests.get(url)
            except:
                print('Failed to load: %s' % url)
                continue
            else:
                downloaded_list_documents.append({
                    'url': url,
                    'content': result.content,
                })

        for doc in downloaded_list_documents:
            self.parse_pages_list(doc['content'])

    def parse_pages_list(self, content):
        document = pq(content)
        links = document('a.detLink')
        for link in links:
            url = link.attrib['href']
            match = self.path_re.search(url)
            if not match:
                continue

            short_url = match.group(1)
            id = match.group(2)

            self.inserted_ids.append(
                insert_page(id, short_url, url)
            )


if __name__ == '__main__':
    args = argument_parser.parse_args()
    parser = ParsePagesList(db, args)
    parser.parse_documents()
