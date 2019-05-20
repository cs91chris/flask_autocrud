import pytest

from flask import Flask
from flask import json
from flask import Response as Resp

from flask.testing import FlaskClient
from werkzeug.utils import cached_property

from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def app():
    class Response(Resp):
        @cached_property
        def json(self):
            return json.loads(self.data)

    class TestClient(FlaskClient):
        def open(self, *args, **kwargs):
            if 'json' in kwargs:
                kwargs['data'] = json.dumps(kwargs.pop('json'))
                kwargs['Content-Type'] = 'application/json'
            return super(TestClient, self).open(*args, **kwargs)

        def fetch(self, url, data=None, *args, **kwargs):
            return self.open(
                url,
                method='FETCH',
                data=json.dumps(data) if data else None,
                *args, **kwargs
            )

    _app = Flask(__name__)
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///tests/db.sqlite3'

    db = SQLAlchemy(_app)
    autocrud = AutoCrud(_app, db)
    _app.response_class = Response
    _app.test_client_class = TestClient
    _app.testing = True
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def assert_pagination(res, code, page, limit):
    assert res.status_code == code
    assert res.headers.get('Pagination-Page') == page
    assert res.headers.get('Pagination-Page-Size') == limit
    assert res.headers.get('Pagination-Count') is not None
    assert res.headers.get('Pagination-Num-Pages') is not None
    assert res.headers.get('Link') != ''

    data = res.get_json()
    assert '_meta' in data
    assert all(e in data['_meta'].keys() for e in (
        "first",
        "last",
        "next",
        "prev"
    ))


def assert_export(res, filename):
    assert res.headers.get('Total-Rows') is not None
    assert res.headers.get('Total-Columns') is not None
    assert res.headers.get('Content-Type') == 'text/csv; charset=utf-8'
    assert res.headers.get('Content-Disposition') == 'attachment; filename={}.csv'.format(filename)


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == 404


def test_resources_list_json(client):
    res = client.get('/resources')
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'


def test_resources_list_xml(client):
    res = client.get(
        '/resources',
        headers={'Accept': 'application/xml'}
    )
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'


def test_resource_crud(client):
    res = client.post(
        '/artist',
        data=json.dumps({'Name': 'pippo'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 201
    assert res.headers.get('Content-Type') == 'application/json'

    data = res.get_json()
    id = data.get('ArtistId')

    etag = res.headers.get('ETag')
    assert etag is not None
    assert res.headers.get('Location').endswith('/artist/{}'.format(id))

    res = client.post(
        '/artist',
        data=json.dumps({'Name': 'pippo'}),
        headers={'Accept': 'application/xml', 'Content-Type': 'application/json'}
    )
    assert res.status_code == 409
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'

    res = client.get('/artist/{}'.format(id))
    etag = res.headers.get('ETag')

    assert res.status_code == 200
    assert etag is not None
    assert res.headers.get('Content-Type') == 'application/json'
    assert res.headers.get('Link') == "</artist/{id}>; rel=self, </artist/{id}/album>; rel=related".format(id=id)

    data = res.get_json()
    returned_id = data.get('ArtistId')
    assert returned_id == id

    res = client.get('/artist/{}'.format(id), headers={'If-None-Match': etag})
    assert res.status_code == 304

    res = client.put(
        '/artist/{}'.format(id),
        data=json.dumps({'Name': 'pippo2'}),
        headers={'Content-Type': 'application/json', 'If-Match': etag}
    )
    etag = res.headers.get('ETag')
    assert res.status_code == 200
    assert etag is not None

    res = client.patch(
        '/artist/{}'.format(id),
        data=json.dumps({'Name': 'pippo3'}),
        headers={'Content-Type': 'application/json', 'If-Match': etag}
    )
    assert res.status_code == 200

    res = client.get('/artist/{}'.format(id), headers={'If-None-Match': etag})
    assert res.status_code == 200

    etag = res.headers.get('ETag')
    res = client.delete('/artist/{}'.format(id))
    assert res.status_code == 428

    res = client.delete('/artist/{}'.format(id), headers={'If-Match': 'fake_etag'})
    assert res.status_code == 412

    res = client.delete('/artist/{}'.format(id), headers={'If-Match': etag})
    assert res.status_code == 204

    res = client.delete('/artist/1000000000')
    assert res.status_code == 404

    res = client.get('/artist/1000000000')
    assert res.status_code == 404


def test_resource_meta(client):
    res = client.get('/artist/meta')
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'

    data = res.get_json()
    assert all(i in data.keys() for i in (
        'name',
        'description',
        'fields',
        'methods',
        'url'
    ))


def test_get_list(client):
    res = client.get('/artist')
    assert res.status_code == 200


def test_hateoas(client):
    res = client.get('/artist/1')
    assert res.status_code == 200

    data = res.get_json()
    assert '_links' in data.keys()
    assert data['_links'].get('self') == '/artist/1'


def test_pagination(client):
    res = client.get('/artist?_page=1&_limit=5')
    assert_pagination(res, 206, '1', '5')


def test_export(client):
    res = client.get('/track?_export=pippo')
    assert res.status_code == 200
    assert_export(res, 'pippo')


def test_extended(client):
    res = client.get('/track/5?_extended')
    assert res.status_code == 200

    data = res.get_json()
    assert data['TrackId'] == 5
    assert all(isinstance(data[e], dict) for e in (
        "Album",
        "Genre",
        "MediaType"
    ))


def test_extended_list(client):
    res = client.get('/track?_extended')
    assert res.status_code == 206

    tracks = 'TrackList'
    data = res.get_json()
    assert data[tracks][0].get('_links') is not None
    assert all(isinstance(data[tracks][0][e], dict) for e in (
        "Album",
        "Genre",
        "MediaType"
    ))


def test_fields(client):
    res = client.get('/artist')
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists][0].keys()) == 3

    res = client.get('/artist?_fields=ArtistId')
    assert res.status_code == 200

    data = res.get_json()
    assert len(data[artists][0].keys()) == 2
    assert all(e in data[artists][0].keys() for e in (
        "ArtistId",
        "_links"
    ))


def test_sorting(client):
    res = client.get('/artist?_sort=ArtistId')
    assert res.status_code == 200

    data = res.get_json()
    first_id = data['ArtistList'][0].get('ArtistId')

    res = client.get('/artist?_sort=-ArtistId')
    assert res.status_code == 200

    data = res.get_json()
    last_id = data['ArtistList'][0].get('ArtistId')
    assert last_id != first_id


def test_comparator(client):
    res = client.get('/invoice?Total=__gt__25')
    assert res.status_code == 200

    invoices = 'InvoiceList'
    data = res.get_json()
    assert len(data[invoices]) == 1

    res = client.get('/invoice?Total=__gte__25')
    assert res.status_code == 200

    invoices = 'InvoiceList'
    data = res.get_json()
    assert len(data[invoices]) == 1

    res = client.get('/artist?ArtistId=__lte__2')
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists]) == 2

    res = client.get('/artist?ArtistId=__lt__2')
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists]) == 1
    assert data[artists][0].get('ArtistId') == 1

    links = data[artists][0].get('_links')
    assert links is not None
    assert links.get('Album') == "/artist/1/album"
    assert links.get('self') == "/artist/1"

    meta = data['_meta']
    assert meta is not None
    assert all(v is None for v in meta.values())
    assert all(e in meta.keys() for e in (
        "first",
        "last",
        "prev",
        "next"
    ))


def test_like(client):
    res = client.get('/album?Title=%...%')
    assert res.status_code == 200

    albums = 'AlbumList'
    data = res.get_json()[albums][0]
    assert data['Title'].startswith('...')

    res = client.get('/album?Title=%%z')
    assert res.status_code == 200

    data = res.get_json()[albums][0]
    assert data['Title'].endswith('z')

    res = client.get('/artist?_sort=Name&Name=!%A%')
    assert res.status_code == 200

    albums = 'ArtistList'
    data = res.get_json()[albums][0]
    assert data['Name'].startswith('B')


def test_range(client):
    res = client.get('/artist?ArtistId=(1;3)')
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists]) == 3
    assert data[artists][0].get('ArtistId') == 1
    assert data[artists][1].get('ArtistId') == 2
    assert data[artists][2].get('ArtistId') == 3

    res = client.get('/invoice?InvoiceDate=!(2008-01-01;2013-12-20 00:00:00)')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['InvoiceList']) == 1


def test_null(client):
    res = client.get('/artist?ArtistId=null')
    assert res.status_code == 200

    data = res.get_json()
    assert len(data['ArtistList']) == 0

    res = client.get('/track?AlbumId=!null')
    assert res.status_code == 206

    data = res.get_json()
    meta = data.get('_meta')
    assert meta['first'] is None
    assert meta['prev'] is None
    assert meta['next'] == "/track?_page=2&_limit=1000"
    assert meta['last'] == "/track?_page=4&_limit=1000"


def test_query_string_invalid(client):
    res = client.get('/invoice?_fields=pippo&_sort=pluto&paperino=1')
    assert res.status_code == 400

    data = res.get_json()
    assert 'invalid' in data and len(data['invalid']) == 3
    assert all(e in data['invalid'] for e in (
        'pippo',
        'pluto',
        'paperino'
    ))


def test_fetch(client):
    res = client.fetch('/artist')
    assert res.status_code == 200

    res = client.fetch('/artist?_export=pippo')
    assert res.status_code == 200
    assert_export(res, 'pippo')

    res = client.fetch('/artist?_page=1&_limit=5')
    assert_pagination(res, 206, '1', '5')


def test_related(client):
    res = client.fetch(
        '/artist',
        data={"related": {"Album": ["*"]}},
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    data = res.get_json()
    assert data['ArtistList'][0].get('AlbumList') is not None


def test_filter(client):
    res = client.fetch(
        '/artist',
        data={
            "filters": [
                {
                    "model": "Artist",
                    "field": "ArtistId",
                    "op": "==",
                    "value": 1
                }
            ]
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists]) == 1
    assert data[artists][0].get('ArtistId') == 1


def test_validators(client):
    res = client.fetch(
        '/customer',
        data={
            "fields": "CustomerId",
            "related": {
                "Employee": "*",
                "Invoice": [1, 2, 3]
            },
            "filters": [
                {
                    "mode": "Invoice",
                    "fiel": "InvoiceDate",
                    "o": ">=",
                    "valu": "2010-04-01T00:00:00"
                }
            ],
            "sorting": [
                {
                    "mode": 1,
                    "fiel": "Total",
                    "directio": "asc"
                }
            ]
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 422

    data = res.get_json()
    mess = data.get('message')
    assert all(e in mess for e in (
        "fields",
        "related",
        "sorting.0.field",
        "sorting.0.model",
        "sorting.0.direction",
        "filters.0.field",
        "filters.0.model",
        "filters.0.value"
    ))

    res = client.fetch(
        '/customer',
        data={
            "filters": 1,
            "related": 2
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 422

    data = res.get_json()
    mess = data.get('message')
    assert 'filters' in mess
    assert 'related' in mess

    res = client.fetch(
        '/artist',
        data={
            "filters": [
                {
                    "model": "Artist",
                    "field": "pluto",
                    "op": "==",
                    "value": 1
                }
            ]
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 400

    data = res.get_json()
    assert 'invalid' in data and len(data['invalid']) == 1
    assert 'pluto' in data['invalid']

    res = client.fetch(
        '/customer',
        data={
            "fields": ["pippo"],
            "related": {
                "Employee": ["pluto"],
                "Invoice": ["paperino"]
            }
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 400

    data = res.get_json()
    assert 'invalid' in data and len(data['invalid']) == 3
    assert all(e in data['invalid'] for e in (
        "pippo",
        "pluto",
        "paperino"
    ))


def test_subresource(client):
    res = client.get('/album/5/track?_extended')
    assert res.status_code == 200

    data = res.get_json()['TrackList'][0]
    assert data['AlbumId'] == 5
    assert all(e in data.keys() for e in (
        "TrackId",
        "GenreId",
        "MediaTypeId",
        "Album",
        "Genre",
        "MediaType"
    ))


def test_check_etag_list(client):
    res = client.get('/album/5/track?_extended')

    etag = res.headers.get('ETag')
    assert res.status_code == 200
    assert etag is not None

    res = client.get('/album/5/track?_extended', headers={'If-None-Match': etag})
    assert res.status_code == 304
