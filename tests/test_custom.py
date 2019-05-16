import pytest

from flask import Flask
from flask import json
from flask import Response as Resp

from flask.testing import FlaskClient
from werkzeug.utils import cached_property

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from flask_autocrud import Model
from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class artists(db.Model, Model):
    __tablename__ = "Artist"
    __description__ = 'artists'
    id = db.Column('ArtistId', db.Integer, primary_key=True, comment='primarykey')
    name = db.Column('Name', db.String(80), unique=True, nullable=False)


class albums(db.Model, Model):
    __tablename__ = "Album"
    id = db.Column('AlbumId', db.Integer, primary_key=True)
    title = db.Column('Title', db.String(80), unique=True, nullable=False)
    artist_id = db.Column('ArtistId', db.Integer, ForeignKey("Artist.ArtistId"), nullable=False)
    artists = relationship(artists, backref="albums")


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
    db.init_app(_app)
    _app.response_class = Response
    _app.test_client_class = TestClient
    _app.testing = True

    autocrud = AutoCrud(_app, db, models=[artists, albums])
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == 404


def test_resource_crud(client):
    res = client.post(
        '/artists',
        data=json.dumps({'name': 'pippo'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 201
    assert res.headers.get('Content-Type') == 'application/json'

    data = json.loads(res.data)
    id = data.get('id')

    assert res.headers.get('Location').endswith('/artists/{}'.format(id))

    res = client.post(
        '/artists',
        data=json.dumps({'name': 'pippo'}),
        headers={'Accept': 'application/xml', 'Content-Type': 'application/json'}
    )
    assert res.status_code == 409
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'

    res = client.get('/artists/{}'.format(id))
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'
    assert res.headers.get('Link') == "</artists/{}>; rel=self".format(id)

    data = json.loads(res.data)
    returned_id = data.get('id')
    assert returned_id == id

    res = client.put(
        '/artists/{}'.format(id),
        data=json.dumps({'name': 'pippo2'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    res = client.patch(
        '/artists/{}'.format(id),
        data=json.dumps({'name': 'pippo3'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    res = client.delete('/artists/{}'.format(id))
    assert res.status_code == 204


def test_resource_meta(client):
    res = client.get('/artists/meta')
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'

    data = json.loads(res.data)
    assert all(i in data.keys() for i in (
        'name',
        'description',
        'fields',
        'methods',
        'url'
    ))
    assert data.get('description') == 'artists'


def test_hateoas(client):
    res = client.get('/artists/1')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert '_links' in data.keys()
    assert data['_links'].get('self') == '/artists/1'


def test_extended(client):
    res = client.get('/albums/5?_extended')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert data['id'] == 5
    assert isinstance(data["artists"], dict)


def test_extended_list(client):
    res = client.get('/albums?_extended')
    assert res.status_code == 200

    data = json.loads(res.data)[0]
    assert isinstance(data["artists"], dict)
    assert data.get('_links') is not None


def test_fields(client):
    res = client.get('/artists')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data[0].keys()) == 3

    res = client.get('/artists?_fields=id')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data[0].keys()) == 2
    assert all(e in data[0].keys() for e in (
        "id",
        "_links"
    ))


def test_sorting(client):
    res = client.get('/artists?_sort=id')
    assert res.status_code == 200

    data = json.loads(res.data)
    first_id = data[0].get('id')

    res = client.get('/artists?_sort=-id')
    assert res.status_code == 200

    data = json.loads(res.data)
    last_id = data[0].get('id')
    assert last_id != first_id


def test_range(client):
    res = client.get('/artists?id=(1;3)')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data) == 3
    assert data[0].get('id') == 1
    assert data[1].get('id') == 2
    assert data[2].get('id') == 3


def test_null(client):
    res = client.get('/artists?id=null')
    assert res.status_code == 200

    data = json.loads(res.data)
    assert len(data) == 0


def test_related(client):
    res = client.fetch(
        '/albums',
        data={"related": {"artists": ["*"]}},
        headers={'Content-Type': 'application/json'}
    )
    assert res.status_code == 200

    data = json.loads(res.data)
    assert data[0].get('artists') is not None


def test_filter(client):
    res = client.fetch(
        '/artists',
        data={
            "filters": [
                {
                    "model": "artists",
                    "field": "id",
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
    assert data[0].get('id') == 1
