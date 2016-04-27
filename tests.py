#!/usr/bin/env python

from unittest.mock import (
    ANY,
    MagicMock,
)

import pytest

from lookup import (
    Mongo,
    ParsePagesList,
)


TEST_ID = 42
TEST_SHORT_URL = '/url/'
TEST_URL = '/long/url/'


def test_insert_page():
    mongo_client = MagicMock()
    mongo_client.tpbmeta = MagicMock()
    mongo_client.tpbmeta.pages.insert_one = MagicMock()
    mongo_client.tpbmeta.pages.insert_one.return_value = 'test_value'
    mongo_insert = mongo_client.tpbmeta.pages.insert_one

    mongo = Mongo(mongo_client)
    parse = ParsePagesList(mongo, None)
    parse.insert_page(TEST_ID, TEST_SHORT_URL, TEST_URL)

    mongo_insert.assert_called_with({
        'url': TEST_URL,
        'short_url': TEST_SHORT_URL,
        'torrent_id': TEST_ID,
        'added_at': ANY,
    })


if __name__ == '__main__':
    pytest.main('tests.py')
