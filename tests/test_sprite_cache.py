"""No real Internet in these tests; every external operation is replaced."""
import json

import pytest

from app import sprite_cache

URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/25.png'
PNG = b'\x89PNG\r\n\x1a\n' + b'pretend-small-image'


def test_sprite_cached_on_disk_and_reused_across_calls(client, monkeypatch):
    calls = []

    def downloader(url, maximum):
        calls.append(url)
        return PNG

    monkeypatch.setattr(sprite_cache, '_request_bytes', downloader)
    for _ in range(3):
        response = client.get('/api/sprites/image', params={'url': URL})
        assert response.status_code == 200
        assert response.content == PNG
        assert response.headers['content-type'].startswith('image/png')
    assert calls == [URL]
    status = client.get('/api/sprites/cache-status').json()
    assert status['images'] == 1
    assert status['bytes'] == len(PNG)
    monkeypatch.setenv('OPTPOKE_SPRITES_OFFLINE', '1')
    assert client.get('/api/sprites/image', params={'url': URL}).status_code == 200
    assert len(calls) == 1


def test_missing_sprites_are_negative_cached(client, monkeypatch):
    called = 0

    def downloader(url, maximum):
        nonlocal called
        called += 1
        raise sprite_cache.MissingRemoteSprite()

    monkeypatch.setattr(sprite_cache, '_request_bytes', downloader)
    for _ in range(3):
        assert client.get('/api/sprites/image', params={'url': URL}).status_code == 404
    assert called == 1
    assert client.get('/api/sprites/cache-status').json()['missing'] == 1


@pytest.mark.parametrize('url', [
    'http://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png',
    'https://127.0.0.1/sprites/25.png',
    'https://play.pokemonshowdown.com/sprites/../../etc/passwd.png',
    'https://play.pokemonshowdown.com/sprites/dex/x.svg',
    'https://play.pokemonshowdown.com/sprites/dex/x.png?override=1',
    'https://raw.githubusercontent.com/other/project/master/pokemon/25.png',
    'https://play.pokemonshowdown.com.evil.example/sprites/dex/25.png',
])
def test_only_approved_direct_sprite_urls(client, monkeypatch, url):
    monkeypatch.setattr(sprite_cache, '_request_bytes', lambda *_: pytest.fail('Unexpected external call'))
    assert client.get('/api/sprites/image', params={'url': url}).status_code == 400


def test_variety_metadata_is_cached_and_does_not_make_browser_fetch_directly(client, monkeypatch):
    calls = []
    def downloader(url, maximum):
        calls.append(url)
        return json.dumps({'sprites':{
            'front_shiny': URL,
            'front_default': 'https://not-allowed.example/25.png',
            'other': {'home': {'front_shiny': URL, 'front_default': None}}
        }}).encode()
    monkeypatch.setattr(sprite_cache, '_request_bytes', downloader)
    for _ in range(2):
        response = client.get('/api/sprites/variety/pikachu-rock-star')
        assert response.status_code == 200
        assert response.json() == {'shiny': URL, 'normal': None}
    assert calls == ['https://pokeapi.co/api/v2/pokemon/pikachu-rock-star']
    monkeypatch.setenv('OPTPOKE_SPRITES_OFFLINE', '1')
    assert client.get('/api/sprites/variety/pikachu-rock-star').status_code == 200


def test_unseen_image_stays_offline(client, monkeypatch):
    monkeypatch.setenv('OPTPOKE_SPRITES_OFFLINE', '1')
    monkeypatch.setattr(sprite_cache, '_request_bytes', lambda *_: pytest.fail('Network called in offline mode'))
    assert client.get('/api/sprites/image', params={'url': URL}).status_code == 503
    assert client.get('/api/sprites/variety/pikachu-rock-star').status_code == 503


def test_temporary_errors_are_not_canonical_missing_images(client, monkeypatch):
    calls = 0
    def downloader(*_):
        nonlocal calls
        calls += 1
        raise sprite_cache.RemoteSpriteUnavailable('temporary')
    monkeypatch.setattr(sprite_cache, '_request_bytes', downloader)
    assert client.get('/api/sprites/image', params={'url': URL}).status_code == 503
    assert client.get('/api/sprites/cache-status').json()['missing'] == 0
    assert calls == 1
