import pytest

from . import create_app
from .models import albums, artists


@pytest.fixture
def app():
    return create_app(
        m=[albums, artists],
        conf={'AUTOCRUD_CONDITIONAL_REQUEST_ENABLED': False}
    )


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_resource_crud(client):
    res = client.post(
        '/artists',
        json={'name': 'pippo'}
    )
    assert res.status_code == 201
    assert res.headers.get('Content-Type') == 'application/json'
    assert res.headers.get('ETag') is None

    data = res.get_json()
    id = data.get('id')

    assert res.headers.get('Location').endswith('/artists/{}'.format(id))

    res = client.post(
        '/artists',
        json={'name': 'pippo'},
        headers={'Accept': 'application/xml'}
    )
    assert res.status_code == 409
    assert res.headers.get('Content-Type') == 'application/xml; charset=utf-8'

    res = client.get('/artists/{}'.format(id))
    assert res.status_code == 200
    assert res.headers.get('ETag') is None
    assert res.headers.get('Content-Type') == 'application/json'
    assert res.headers.get('Link') == "</artists/{id}>; rel=self, </artists/{id}/myalbum>; rel=related".format(id=id)

    data = res.get_json()
    returned_id = data.get('id')
    assert returned_id == id

    res = client.put(
        '/artists/{}'.format(id),
        json={'name': 'pippo2'}
    )
    assert res.status_code == 200
    assert res.headers.get('ETag') is None

    res = client.patch(
        '/artists/{}'.format(id),
        json={'name': 'pippo3'}
    )
    assert res.status_code == 200
    assert res.headers.get('ETag') is None

    res = client.delete('/artists/{}'.format(id))
    assert res.status_code == 204


def test_resource_meta(client):
    res = client.get('/artists/meta')
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
    assert data.get('description') == 'artists'


def test_hateoas(client):
    res = client.get('/artists/1')
    assert res.status_code == 200

    data = res.get_json()
    assert '_links' in data.keys()
    assert data['_links'].get('self') == '/artists/1'


def test_extended(client):
    res = client.get('/myalbum/5?_related')
    assert res.status_code == 200

    data = res.get_json()
    assert data['id'] == 5
    assert isinstance(data["artists"], dict)


def test_extended_list(client):
    res = client.get('/myalbum?_related=artists')
    assert res.status_code == 200

    data = res.get_json()['albumsList'][0]
    assert isinstance(data["artists"], dict)
    assert data.get('_links') is not None


def test_fields(client):
    res = client.get('/artists')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    assert len(data[0].keys()) == 3

    res = client.get('/artists?_fields=id')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    assert len(data[0].keys()) == 2
    assert all(e in data[0].keys() for e in (
        "id",
        "_links"
    ))


def test_sorting(client):
    res = client.get('/artists?_sort=id')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    first_id = data[0].get('id')

    res = client.get('/artists?_sort=-id')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    last_id = data[0].get('id')
    assert last_id != first_id


def test_range(client):
    res = client.get('/artists?id=(1;3)')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    assert len(data) == 3
    assert data[0].get('id') == 1
    assert data[1].get('id') == 2
    assert data[2].get('id') == 3


def test_null(client):
    res = client.get('/artists?id=null')
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    assert len(data) == 0


def test_related(client):
    res = client.fetch(
        '/myalbum',
        json={"related": {"artists": ["*"]}}
    )
    assert res.status_code == 200

    data = res.get_json()['albumsList']
    assert data[0].get('artists') is not None


def test_filter(client):
    res = client.fetch(
        '/artists',
        json={
            "filters": [
                {
                    "model": "artists",
                    "field": "id",
                    "op": "==",
                    "value": 1
                }
            ]
        }
    )
    assert res.status_code == 200

    data = res.get_json()['artistsList']
    assert len(data) == 1
    assert data[0].get('id') == 1


def test_subresource(client):
    res = client.get('/artists/1/myalbum?_related')
    assert res.status_code == 200

    data = res.get_json()['albumsList'][0]
    assert data['artist_id'] == 1
    assert all(e in data.keys() for e in (
        "id",
        "artists"
    ))


def test_hidden_field(client):
    res = client.get('/myalbum/5')
    assert res.status_code == 200

    data = res.get_json()
    assert data['id'] == 5
    assert len(data.keys()) == 3

    res = client.get('/myalbum?_fields=title;__dict__')
    assert res.status_code == 400

    data = res.get_json()
    assert data['response']['invalid'] == ['title', '__dict__']

    res = client.get('/myalbum/meta')
    assert res.status_code == 200

    data = res.get_json()
    assert len(data['fields']) == 2
