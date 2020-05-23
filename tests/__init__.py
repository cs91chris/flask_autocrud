from flask import Flask
from flask.testing import FlaskClient

from flask_autocrud import AutoCrud
from tests.models import db


def create_app(m=None, conf=None):
    class TestClient(FlaskClient):
        def fetch(self, url, *args, **kwargs):
            return self.open(url, method='FETCH', *args, **kwargs)

    _app = Flask(__name__)
    _app.config['DEBUG'] = True
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///tests/db.sqlite3'
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['ERROR_FORCE_CONTENT_TYPE'] = False
    _app.config.update(**(conf or {}))

    with _app.app_context():
        db.init_app(_app)
        AutoCrud(_app, db, models=m)

    _app.test_client_class = TestClient
    _app.testing = True
    return _app


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
