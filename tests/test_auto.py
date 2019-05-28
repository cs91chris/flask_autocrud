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


def test_bad_request(client):
    res = client.post('/artist')
    assert res.status_code == 400


def test_not_found(client):
    res = client.delete('/artist/1000000000')
    assert res.status_code == 404

    res = client.get('/artist/1000000000')
    assert res.status_code == 404


def test_conflict(client):
    res = client.post(
        '/artist',
        json={'Name': 'Accept'},
        headers={'Accept': 'application/xml'}
    )
    assert res.status_code == 409
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'


def test_update(client):
    res = client.get('/artist/1')
    etag = res.headers.get('ETag')

    res = client.put(
        '/artist/1',
        json={'Name': 'pippo2'},
        headers={'If-Match': etag}
    )
    etag = res.headers.get('ETag')
    assert res.status_code == 200
    assert etag is not None

    res = client.patch(
        '/artist/1',
        json={'Name': 'pippo3'},
        headers={'If-Match': etag}
    )
    assert res.status_code == 200


def test_unprocessable_entity(client):
    res = client.post(
        '/artist',
        json={'pippo': 'pluto'}
    )
    assert res.status_code == 422
    assert res.headers.get('Content-Type') == 'application/json'

    res = client.put(
        '/artist/1',
        json={'pippo': 'pluto'}
    )
    assert res.status_code == 422
    assert res.headers.get('Content-Type') == 'application/json'

    res = client.patch(
        '/artist/1',
        json={'pippo': 'pluto'}
    )
    assert res.status_code == 422
    assert res.headers.get('Content-Type') == 'application/json'


def test_resource_crud(client):
    res = client.post(
        '/artist',
        json={'Name': 'pippo'}
    )
    assert res.status_code == 201
    assert res.headers.get('Content-Type') == 'application/json'

    data = res.get_json()
    id = data.get('ArtistId')

    etag = res.headers.get('ETag')
    assert etag is not None
    assert res.headers.get('Location').endswith('/artist/{}'.format(id))

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

    res = client.get('/artist/{}'.format(id), headers={'If-None-Match': 'fake_etag'})
    assert res.status_code == 200

    etag = res.headers.get('ETag')
    res = client.delete('/artist/{}'.format(id))
    assert res.status_code == 428

    res = client.delete('/artist/{}'.format(id), headers={'If-Match': 'fake_etag'})
    assert res.status_code == 412

    res = client.delete('/artist/{}'.format(id), headers={'If-Match': etag})
    assert res.status_code == 204


def test_put_creation(client):
    res = client.put(
        '/some_model/10',
        json={'value': 'pippo'}
    )
    assert res.status_code == 201
    etag = res.headers.get('ETag')
    assert etag is not None
    assert res.get_json().get('id') == 10

    res = client.delete('/some_model/10', headers={'If-Match': etag})
    assert res.status_code == 204


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


def test_export(client):
    res = client.get('/track?_export=pippo')
    assert res.status_code == 200
    assert_export(res, 'pippo')


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
        json={
            "filters": 1,
            "related": 2
        }
    )
    assert res.status_code == 422

    data = res.get_json()
    mess = data.get('message')
    assert 'filters' in mess
    assert 'related' in mess

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

    data = res.get_json()
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
