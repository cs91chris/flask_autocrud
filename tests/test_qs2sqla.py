import pytest

from . import assert_pagination, create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_pagination(client):
    res = client.get('/artist?_page=1&_limit=5')
    assert_pagination(res, 206, '1', '5')

    res = client.get('/artist?_page=3&_limit=100')
    assert_pagination(res, 200, '3', '100')

    res = client.get('/artist?_page=100&_limit=100')
    assert res.status_code == 204
    assert res.headers.get('Links') is None


def test_extended(client):
    res = client.get('/track/5?_related')
    assert res.status_code == 200

    data = res.get_json()
    assert data['TrackId'] == 5
    assert all(isinstance(data[e], dict) for e in (
        "Album",
        "Genre",
        "MediaType"
    ))

    res = client.get('/track/5?_related=Album')
    assert res.status_code == 200

    data = res.get_json()
    assert data['TrackId'] == 5
    assert 'Album' in data
    assert 'MediaType' not in data


def test_extended_list(client):
    res = client.get('/track?_related')
    assert res.status_code == 206

    tracks = 'TrackList'
    data = res.get_json()
    assert data[tracks][0].get('_links') is not None
    assert all(isinstance(data[tracks][3][e], dict) for e in (
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
    res = client.get('/invoice?_fields=pippo&_sort=pluto&paperino=1&invalid=true&_page=a&_limit=a')
    assert res.status_code == 400

    data = res.get_json()['response']
    assert 'invalid' in data and len(data['invalid']) == 6
    assert all(e in data['invalid'] for e in (
        'pippo',
        'pluto',
        'paperino',
        'invalid',
        '_page',
        '_limit',
    ))


def test_check_etag_list(client):
    res = client.get('/album/5/track?_related')

    etag = res.headers.get('ETag')
    assert res.status_code == 200
    assert etag is not None

    res = client.get('/album/5/track?_related', headers={'If-None-Match': etag})
    assert res.status_code == 304
