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
    assert all(i in data.keys() for i in ('description', 'fields', 'methods', 'url'))
    assert data.get('description') == 'artists'
