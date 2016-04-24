#!/usr/bin/env python

import argparse
import time
from datetime import datetime

from pymongo import MongoClient

mongo_client = MongoClient()
db = mongo_client.tpbmeta

argument_parser = argparse.ArgumentParser(
    description='Add a URL to DB for later processing.'
)
argument_parser.add_argument(
    'URL', help='A URL to add.'
)


def insert_page(url):
    result = db.pages.insert_one({
        'url': url,
        'added_at': time.mktime(datetime.utcnow().timetuple()),
    })
    return result


if __name__ == '__main__':
    args = argument_parser.parse_args()
    print(insert_page(args.URL).inserted_id)
