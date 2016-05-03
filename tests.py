#!/usr/bin/env python

from contextlib import contextmanager
from http import HTTPStatus
from unittest.mock import (
    ANY,
    MagicMock,
    patch,
)

import pytest
from testfixtures import LogCapture

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
    fake_urls = ['fake_url']

    def test_ok(self):
        parser = self.create_parser()
        response = produce_requests_response_object(HTTPStatus.OK, TEST_HTML)
        with patch(
            'requests.get',
            return_value=response
        ):
            parser.parse_documents()

        assert len(parser.inserted_ids) == 2

    def test_404(self):
        parser = self.create_parser()
        response = produce_requests_response_object(HTTPStatus.NOT_FOUND, '')
        expected_log_message = (
            'Failed to load: %s. status_code=%s' % (
                self.fake_urls[0],
                HTTPStatus.NOT_FOUND,
            )
        )
        with patch(
            'requests.get',
            return_value=response
        ):
            with self.assert_log_item('ERROR', expected_log_message):
                parser.parse_documents()

    def create_parser(self, mongo=None, urls=None):
        if mongo is None:
            mongo = create_mongo()

        if urls is None:
            urls = self.fake_urls[:]

        return ParsePagesList(mongo, urls)

    @contextmanager
    def assert_log_item(self, level, message):
        with LogCapture() as log:
            yield

            log.check((ANY, level, message, ))


if __name__ == '__main__':
    pytest.main('tests.py')
