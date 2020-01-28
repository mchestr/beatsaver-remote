import asyncio
import logging
import os
from functools import wraps
from os.path import join

import simplejson as json
from sanic import Blueprint, response

from bsr.song_download import download

CURRENT_WEBSOCKETS = []
LINKS_SUBMITTED = {}

blueprint = Blueprint('api')
log = logging.getLogger(__name__)


@blueprint.route('/', methods=['GET'])
@blueprint.route('/<path:path>', methods=['GET'])
async def index(request, path='index.html'):
    filepath = join(os.getcwd(), 'web', 'dist', path)
    return await response.file(filepath)


def remove_on_failure(func):
    @wraps(func)
    async def on_call(ws, *args, **kwargs):
        try:
            await func(ws, *args, **kwargs)
        except Exception as exc:
            log.exception(exc)
            CURRENT_WEBSOCKETS.remove(ws)

    return on_call


@remove_on_failure
async def notify_link_state(ws, id_, state):
    if id_ in LINKS_SUBMITTED:
        LINKS_SUBMITTED[id_]['state'] = state
    await ws.send(json.dumps({'type': 'link-state', 'id': id_, 'state': state}))


@remove_on_failure
async def notify_link_submit(ws, data):
    data['state'] = 'submitted'
    LINKS_SUBMITTED[data['id']] = data
    await ws.send(json.dumps(data))


@remove_on_failure
async def notify_link_name(ws, id_, name):
    data = dict(type='link-name', id=id_, name=name)
    LINKS_SUBMITTED[id_]['name'] = name
    await ws.send(json.dumps(data))


@remove_on_failure
async def handle_websocket(ws, config):
    await ws.send(json.dumps({'type': 'links', 'links': list(LINKS_SUBMITTED.values())}))
    while True:
        data = json.loads(await ws.recv())
        if data['type'] == 'link-submit':
            LINKS_SUBMITTED[data['id']] = data
            await asyncio.gather(*[notify_link_submit(socket, data) for socket in CURRENT_WEBSOCKETS if socket != ws])
            try:
                new_folder = await download(config, data)
                await asyncio.gather(*[notify_link_name(ws, data['id'], new_folder) for ws in CURRENT_WEBSOCKETS])
            except Exception:
                log.exception('unknown_exception')
                await asyncio.gather(*[notify_link_state(ws, data['id'], 'error') for ws in CURRENT_WEBSOCKETS])
                return
            await asyncio.gather(*[notify_link_state(ws, data['id'], 'complete') for ws in CURRENT_WEBSOCKETS])


async def websocket(request, ws):
    log.debug('opened websocket')
    CURRENT_WEBSOCKETS.append(ws)
    await handle_websocket(ws, request.app.config.bsr)
