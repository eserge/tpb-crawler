#!/usr/bin/env python

import argparse
import logging
import time
import re
from datetime import datetime
from http import HTTPStatus

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pyquery import PyQuery

import requests
from requests.exceptions import RequestException


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

mongo_client = MongoClient()

loglevel = logging.DEBUG

log_files = {
    logging.DEBUG: 'debug.log',
    logging.ERROR: 'error.log',
}

log_format = '[%(levelname)s]P:%(process)d T:%(thread)d %(asctime)s %(name)s.%(funcName)s: %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(loglevel)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(log_files[loglevel])
file_handler.setLevel(loglevel)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(loglevel)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class Mongo(object):
    db = None

    def __init__(self, mongo_client):
        self.db = mongo_client.tpbmeta

mongo = Mongo(mongo_client)


class ParsePagesList(object):
    path_re = re.compile(r'^.*(\/torrent\/(\d+)\/).*')

    def __init__(self, mongo, urls):
        self.db = mongo.db
        self.urls = urls
        self.inserted_ids = []

    def parse_documents(self):
        downloaded_list_documents = []
        for url in self.urls:
            try:
                result = requests.get(url)
            except RequestException:
                logger.exception('Failed to load: %s', url)
                continue
            if result.status_code != HTTPStatus.OK:
                logger.error(
                    'Failed to load: %s. status_code=%s', url,
                    result.status_code
                )
                continue

            logger.debug(
                'Requested URL (%s) is downloaded, starting to work on it.'
            )
            downloaded_list_documents.append({
                'url': url,
                'content': result.content,
            })

        for doc in downloaded_list_documents:
            self.parse_pages_list(doc['content'])

    def parse_pages_list(self, content):
        document = PyQuery(content)
        links = document('a.detLink')
        for link in links:
            url = link.attrib['href']
            id, short_url = self.match_url(url)
            if not id:
                continue

            self.inserted_ids.append(
                self.insert_page(id, short_url, url)
            )

        self.inserted_ids = [
            document_id for document_id in self.inserted_ids
            if document_id is not None
        ]

    def match_url(self, url):
        match = self.path_re.search(url)
        if not match:
            return None, None

        return match.group(2), match.group(1)

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
    logger.info('Added %(number)s document%(ending)s' % {
        'number': number, 'ending': plural_ending,
    })
