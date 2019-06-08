import pytest

from . import create_app
from . import assert_export
from . import assert_pagination


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


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
        json={"related": {"Album": ["*"]}}
    )
    assert res.status_code == 200

    data = res.get_json()
    assert data['ArtistList'][0].get('AlbumList') is not None


def test_filter(client):
    res = client.fetch(
        '/artist',
        json={
            "filters": [
                {
                    "model": "Artist",
                    "field": "ArtistId",
                    "op": "==",
                    "value": 1
                }
            ]
        }
    )
    assert res.status_code == 200

    artists = 'ArtistList'
    data = res.get_json()
    assert len(data[artists]) == 1
    assert data[artists][0].get('ArtistId') == 1


def test_validators(client):
    res = client.fetch(
        '/customer',
        json={
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
        }
    )
    assert res.status_code == 422

    data = res.get_json()['response']
    assert all(e in data for e in (
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
        json={
            "filters": 1,
            "related": 2
        }
    )
    assert res.status_code == 422

    data = res.get_json()['response']
    assert 'filters' in data
    assert 'related' in data

    res = client.fetch(
        '/artist',
        json={
            "filters": [
                {
                    "model": "Artist",
                    "field": "pluto",
                    "op": "==",
                    "value": 1
                }
            ]
        }
    )
    assert res.status_code == 400

    data = res.get_json()['response']
    assert 'invalid' in data and len(data['invalid']) == 1
    assert 'pluto' in data['invalid']

    res = client.fetch(
        '/customer',
        json={
            "fields": ["pippo"],
            "related": {
                "Employee": ["pluto"],
                "Invoice": ["paperino"]
            }
        }
    )
    assert res.status_code == 400

    data = res.get_json()['response']
    assert 'invalid' in data and len(data['invalid']) == 3
    assert all(e in data['invalid'] for e in (
        "pippo",
        "pluto",
        "paperino"
    ))
