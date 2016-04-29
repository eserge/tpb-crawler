#!/usr/bin/env python

import argparse
import time
from datetime import datetime
import re

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pyquery import PyQuery as pq
import requests

mongo_client = MongoClient()

description = (
    'Parses pages on given URLs find links on them and'
    ' adds those to DB for later processing.'
)
argument_parser = argparse.ArgumentParser(
    description=description
)
argument_parser.add_argument(
    'urls', nargs='+', metavar='URLs',
    help='A space-separated list of URLs to parse.'
)


class Mongo(object):
    db = None

    def __init__(self, mongo_client):
        self.db = mongo_client.tpbmeta

mongo = Mongo(mongo_client)


class ParsePagesList(object):
    def __init__(self, mongo, urls):
        self.db = mongo.db
        self.urls = urls
        self.path_re = re.compile(r'^(\/torrent\/(\d+)\/).*')
        self.inserted_ids = []

    def parse_documents(self):
        downloaded_list_documents = []
        for url in self.urls:
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
                self.insert_page(id, short_url, url)
            )

        self.inserted_ids = [
            document_id for document_id in self.inserted_ids
            if document_id is not None
        ]

    def insert_page(self, id, short_url, url):
        result = None
        try:
            result = self.db.pages.insert_one({
                'url': url,
                'short_url': short_url,
                'torrent_id': id,
                'added_at': time.mktime(datetime.utcnow().timetuple()),
            })
        except DuplicateKeyError:
            pass

        return result


if __name__ == '__main__':
    args = argument_parser.parse_args()
    parser = ParsePagesList(mongo, args.urls)
    parser.parse_documents()
    number = len(parser.inserted_ids)
    plural_ending = '' if number == 1 else 's'
    print('Added %(number)s document%(ending)s' % {
        'number': number, 'ending': plural_ending,
    })
