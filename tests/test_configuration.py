import pytest

from . import create_app


@pytest.fixture
def app():
    return create_app(conf={
        'AUTOCRUD_READ_ONLY': True,
        'AUTOCRUD_FETCH_ENABLED': False,
        'AUTOCRUD_EXPORT_ENABLED': False,
        'AUTOCRUD_METADATA_ENABLED': False,
        'AUTOCRUD_RESOURCES_URL_ENABLED': False,
        'AUTOCRUD_CONDITIONAL_REQUEST_ENABLED': False,
        'AUTOCRUD_QUERY_STRING_FILTERS_ENABLED': False,
    })


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_read_only(client):
    res = client.post(
        '/artist',
        json={'Name': 'Accept'}
    )
    assert res.status_code == 405

    res = client.put(
        '/artist/1',
        json={'Name': 'pippo2'}
    )
    assert res.status_code == 405

    res = client.patch(
        '/artist/1',
        json={'Name': 'pippo3'}
    )
    assert res.status_code == 405

    res = client.delete('/artist/1')
    assert res.status_code == 405


def test_get_resource(client):
    res = client.get('/artist/1')
    assert res.status_code == 200

    etag = res.headers.get('ETag')
    assert etag is None

    data = res.get_json()
    assert data.get('ArtistId') == 1


def test_fetch_disabled(client):
    res = client.fetch('/album', json={})
    assert res.status_code == 405


def test_resources_list_disabled(client):
    res = client.get('/resources')
    assert res.status_code == 404


def test_meta_disabled(client):
    res = client.get('/artist/meta')
    assert res.status_code == 404


def test_export_disabled(client):
    res = client.get('/artist?_export=pippo')
    assert res.status_code == 200
    assert res.headers.get('Content-Type') == 'application/json'
