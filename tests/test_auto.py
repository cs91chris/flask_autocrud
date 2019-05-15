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
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///../flask_autocrud/examples/db.sqlite3'

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
    assert res.headers.get('Pagination-Limit') == limit
    assert res.headers.get('Pagination-Count') is not None
    assert res.headers.get('Pagination-Num-Pages') is not None


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

    data = json.loads(res.data)
    id = data.get('ArtistId')

    assert res.headers.get('Location').endswith('/artist/{}'.format(id))

    res = client.post(
        '/artist',
        data=json.dumps({'Name': 'pippo'}),
        headers={'Accept': 'application/xml', 'Content-Type': 'application/json'}
    )
    assert res.status_code == 409
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'

    res = client.get('/artist/{}'.format(id))
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'
    assert res.headers.get('Link') == "</artist/{}>; rel=self".format(id)

    data = json.loads(res.data)
    returned_id = data.get('ArtistId')
    assert returned_id == id

    res = client.put(
        '/artist/{}'.format(id),
        data=json.dumps({'Name': 'pippo2'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    res = client.patch(
        '/artist/{}'.format(id),
        data=json.dumps({'Name': 'pippo3'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    res = client.delete('/artist/{}'.format(id))
    assert res.status_code == 204

    res = client.delete('/artist/1000000000')
    assert res.status_code == 404

    res = client.get('/artist/1000000000')
    assert res.status_code == 404


def test_resource_meta(client):
    res = client.get('/artist/meta')
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'

    data = json.loads(res.data)
    assert all(i in data.keys() for i in ('description', 'fields', 'methods', 'url'))


def test_get_list(client):
    res = client.get('/artist')
    assert res.status_code == 200


def test_hateoas(client):
    res = client.get('/artist/1')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert '_links' in data.keys()
    assert data['_links'].get('self') == '/artist/1'


def test_pagination(client):
    res = client.get('/artist?_page=1&_limit=5')
    assert_pagination(res, 206, '1', '5')


def test_export(client):
    res = client.get('/artist?_export=pippo')
    assert res.status_code == 200
    assert_export(res, 'pippo')


def test_fields(client):
    res = client.get('/artist')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data[0].keys()) == 3

    res = client.get('/artist?_fields=ArtistId')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data[0].keys()) == 2


def test_sorting(client):
    res = client.get('/artist?_sort=ArtistId')
    assert res.status_code == 200

    data = json.loads(res.data)
    first_id = data[0].get('ArtistId')

    res = client.get('/artist?_sort=-ArtistId')
    assert res.status_code == 200

    data = json.loads(res.data)
    last_id = data[0].get('ArtistId')
    assert last_id != first_id


def test_range(client):
    res = client.get('/artist?ArtistId=(1;3)')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data) == 3
    assert data[0].get('ArtistId') == 1
    assert data[1].get('ArtistId') == 2
    assert data[2].get('ArtistId') == 3


def test_null(client):
    res = client.get('/artist?ArtistId=null')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data) == 0


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

    data = json.loads(res.data)
    assert data[0].get('AlbumList') is not None


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

    data = json.loads(res.data)
    assert len(data) == 1
    assert data[0].get('ArtistId') == 1


def test_validators(client):
    res = client.fetch(
        '/customer',
        data={
            "fields": "CustomerId",
            "related": {
                "Employee": "*",
                "Invoice": [1, 2, 3]
            },
            "filters":
                {
                    "model": "Invoice",
                    "field": "InvoiceDate",
                    "op": ">=",
                    "value": "2010-04-01T00:00:00"
                },
            "sorting": [
                {
                    "model": 1,
                    "fiel": "Total",
                    "direction": "asc"
                }
            ]
        },
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 422

    data = json.loads(res.data)
    mess = data.get('message')
    assert all(e in mess for e in (
        "fields",
        "filters",
        "related",
        "sorting.0.field",
        "sorting.0.model"
    ))
