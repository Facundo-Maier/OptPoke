"""On-demand, persistent, allowlisted sprite cache.

The frontend only talks to this local API. External assets are fetched once on
first view and served from a directory outside the Git repository afterwards.
404s are remembered too, so a missing sprite is not requested on every visit.
No image blobs are stored in SQLite and backups stay small.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .db import database_path

MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_API_BYTES = 2 * 1024 * 1024
_ALLOWED_HOSTS = {
    'raw.githubusercontent.com': '/PokeAPI/sprites/master/sprites/pokemon/',
    'play.pokemonshowdown.com': '/sprites/',
}
_URL_SEGMENTS = re.compile(r'^[a-zA-Z0-9_./-]+$')
_VARIETY = re.compile(r'^[a-z0-9-]{1,70}$')
_download_slots = threading.BoundedSemaphore(3)
_key_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


class MissingRemoteSprite(Exception):
    """HTTP 404/410: permanently cache until an explicit cache reset."""


class RemoteSpriteUnavailable(Exception):
    """Temporary network/server error, don't claim the sprite doesn't exist."""


class InvalidSpriteSource(ValueError):
    """Disallowed URL, scheme, path or extension."""


def cache_root() -> Path:
    # Honours OPTPOKE_DATA_DIR, just like the existing SQLite database.
    return database_path().parent / 'sprites'


def offline() -> bool:
    return os.environ.get('OPTPOKE_SPRITES_OFFLINE', '').lower() in ('1', 'true', 'yes')


def validate_image_url(url: str) -> str:
    if len(url) > 400:
        raise InvalidSpriteSource('URL demasiado larga')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        raise InvalidSpriteSource('Solo se permiten URLs HTTPS directas')
    prefix = _ALLOWED_HOSTS.get(parsed.netloc)
    if not prefix or not parsed.path.startswith(prefix):
        raise InvalidSpriteSource('La fuente no está autorizada')
    if parsed.query or parsed.fragment or not _URL_SEGMENTS.fullmatch(parsed.path):
        raise InvalidSpriteSource('La ruta contiene caracteres no permitidos')
    if '..' in parsed.path.split('/') or '//' in parsed.path:
        raise InvalidSpriteSource('Ruta no permitida')
    if not parsed.path.lower().endswith(('.png', '.gif')):
        raise InvalidSpriteSource('Formato no permitido')
    return url


class _SafeRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never let a trusted public URL redirect this local proxy to an
        # intranet, localhost, private IP or another unapproved provider.
        try:
            if req.full_url.startswith('https://pokeapi.co/api/v2/pokemon/'):
                if not newurl.startswith('https://pokeapi.co/api/v2/pokemon/'):
                    return None
            else:
                validate_image_url(newurl)
        except (ValueError, InvalidSpriteSource):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = build_opener(_SafeRedirects)


def _request_bytes(url: str, maximum: int) -> bytes:
    req = Request(url, headers={
        'User-Agent': 'OptPoke/0.1.3 (personal offline-first sprite cache)',
        'Accept': 'image/png,image/gif,application/json',
    })
    try:
        with _opener.open(req, timeout=7) as response:
            length = response.headers.get('Content-Length')
            if length and int(length) > maximum:
                raise RemoteSpriteUnavailable('Imagen demasiado grande')
            contents = response.read(maximum + 1)
            if len(contents) > maximum:
                raise RemoteSpriteUnavailable('Imagen demasiado grande')
            return contents
    except HTTPError as exc:
        if exc.code in (404, 410):
            raise MissingRemoteSprite() from exc
        raise RemoteSpriteUnavailable(f'HTTP {exc.code}') from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RemoteSpriteUnavailable('No se pudo contactar la fuente') from exc


def _paths(key: str, ext: str) -> tuple[Path, Path]:
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
    directory = cache_root() / digest[:2]
    return directory / f'{digest}{ext}', directory / f'{digest}.missing'


def _pause_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + '.retry')


def _respect_pause(path: Path) -> None:
    # Avoid repeated hits to an unreachable provider, across app restarts too.
    if path.is_file() and time.time() - path.stat().st_mtime < 15 * 60:
        raise RemoteSpriteUnavailable('Fuente temporalmente no disponible: reintento diferido')


def _pause(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _key_locks.setdefault(key, threading.Lock())


def cached_image(url: str) -> tuple[bytes, str]:
    """Return exact cached bytes or download once, with persistent misses."""
    url = validate_image_url(url)
    extension = '.gif' if url.lower().endswith('.gif') else '.png'
    media_type = 'image/gif' if extension == '.gif' else 'image/png'
    path, miss = _paths(f'image:{url}', extension)
    with _lock_for(f'image:{url}'):
        if path.is_file():
            return path.read_bytes(), media_type
        if miss.is_file():
            raise MissingRemoteSprite()
        if offline():
            raise RemoteSpriteUnavailable('Modo sin conexión: imagen no guardada')
        pause = _pause_path(path)
        _respect_pause(pause)
        try:
            with _download_slots:
                data = _request_bytes(url, MAX_ASSET_BYTES)
            if extension == '.png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise RemoteSpriteUnavailable('La respuesta no es un PNG válido')
            if extension == '.gif' and not data.startswith((b'GIF87a', b'GIF89a')):
                raise RemoteSpriteUnavailable('La respuesta no es un GIF válido')
        except MissingRemoteSprite:
            miss.parent.mkdir(parents=True, exist_ok=True)
            miss.touch()
            raise
        except RemoteSpriteUnavailable:
            _pause(pause)
            raise
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(extension + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)
        pause.unlink(missing_ok=True)
        return data, media_type


def cached_variety(key: str) -> dict:
    if not _VARIETY.fullmatch(key):
        raise InvalidSpriteSource('Nombre de variedad no válido')
    path, miss = _paths(f'variety:{key}', '.json')
    with _lock_for(f'variety:{key}'):
        if path.is_file():
            return json.loads(path.read_text(encoding='utf-8'))
        if miss.is_file():
            raise MissingRemoteSprite()
        if offline():
            raise RemoteSpriteUnavailable('Modo sin conexión: variedad no guardada')
        pause = _pause_path(path)
        _respect_pause(pause)
        try:
            with _download_slots:
                response = _request_bytes(f'https://pokeapi.co/api/v2/pokemon/{key}', MAX_API_BYTES)
            sprites = json.loads(response)['sprites']
            home = (sprites.get('other') or {}).get('home') or {}
            result = {
                'shiny': home.get('front_shiny') or sprites.get('front_shiny'),
                'normal': home.get('front_default') or sprites.get('front_default'),
            }
        except MissingRemoteSprite:
            miss.parent.mkdir(parents=True, exist_ok=True)
            miss.touch()
            raise
        except RemoteSpriteUnavailable:
            _pause(pause)
            raise
        except (ValueError, TypeError, KeyError) as exc:
            _pause(pause)
            raise RemoteSpriteUnavailable('Respuesta de PokéAPI inesperada') from exc
        for which, image_url in result.items():
            if image_url:
                try:
                    validate_image_url(image_url)
                except InvalidSpriteSource:
                    result[which] = None
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result), encoding='utf-8')
        temporary.replace(path)
        pause.unlink(missing_ok=True)
        return result


def cache_status() -> dict:
    root = cache_root()
    if not root.exists():
        return {'images': 0, 'missing': 0, 'varieties': 0, 'bytes': 0, 'offline': offline()}
    files = list(root.rglob('*'))
    images = [f for f in files if f.is_file() and f.suffix in ('.png', '.gif')]
    return {
        'images': len(images),
        'missing': sum(f.is_file() and f.suffix == '.missing' for f in files),
        'varieties': sum(f.is_file() and f.suffix == '.json' for f in files),
        'bytes': sum(f.stat().st_size for f in images),
        'offline': offline(),
    }
