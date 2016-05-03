#!/usr/bin/env python

from http import HTTPStatus
from unittest.mock import (
    ANY,
    MagicMock,
    patch,
)

import pytest

from lookup import (
    Mongo,
    ParsePagesList,
)


TEST_ID = 42
TEST_SHORT_URL = '/url/'
TEST_URL = '/long/url/'

TEST_HTML = '''
<html>
<head><title>TPB</title></head>
<body>
<div>
    <div>
        <a class="detLink" href="http://example.com/torrent/1/stuff/">1</a>
        <a class="mutiple classes detLink" href="http://example.com/torrent/2/stuff">2</a>
        <a class="detLink" href="http://example.com/abracadabra/3/abyr">3</a>
        <a class="notaDetLink" href="http://example.com/doentmatter/4">4</a>
    </div>
</body>
</html>
'''


def produce_requests_response_object(status_code, content):
    requests_mock = MagicMock()
    requests_mock.status_code = status_code
    requests_mock.content = content

    return requests_mock


def create_mongo():
    def insert_one(self, *args, **kwargs):
        x = 0
        while True:
            x += 1
            yield x

    mongo_client = MagicMock()
    mongo_client.tpbmeta = MagicMock()
    mongo_client.tpbmeta.pages.insert_one = insert_one

    return mongo_client


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


class TestParsePagesList(object):
    def test_ok(self):
        urls = ['fake_url']
        mongo = create_mongo()

        parser = ParsePagesList(mongo, urls)
        response = produce_requests_response_object(HTTPStatus.OK, TEST_HTML)
        with patch(
            'requests.get',
            return_value=response
        ):
            parser.parse_documents()

        assert len(parser.inserted_ids) == 2


if __name__ == '__main__':
    pytest.main('tests.py')
