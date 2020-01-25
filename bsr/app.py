import asyncio
import os
import shutil
import zipfile
from functools import wraps
from os.path import join
from urllib.parse import urlparse

import aiohttp
import simplejson as json
from sanic import Blueprint, Sanic, response
from sanic_cors import CORS

CURRENT_WEBSOCKETS = []
LINKS_SUBMITTED = {}
TEMP_DIR = './temp/'
try:
    os.mkdir(TEMP_DIR)
except IOError:
    pass

blueprint = Blueprint('api')


def new(beatsaber_directory):
    app = Sanic()
    app.blueprint(blueprint)
    app.add_websocket_route(websocket, '/ws')
    CORS(app)
    app.config.CUSTOM_LEVELS_DIR = join(beatsaber_directory, 'Beat Saber_Data', 'CustomLevels')
    return app


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
            print(exc)
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
async def handle_websocket(config, ws):
    await ws.send(json.dumps({'type': 'links', 'links': list(LINKS_SUBMITTED.values())}))
    while True:
        data = json.loads(await ws.recv())
        if data['type'] == 'link-submit':
            LINKS_SUBMITTED[data['id']] = data
            await asyncio.gather(*[notify_link_submit(socket, data) for socket in CURRENT_WEBSOCKETS if socket != ws])
            asyncio.create_task(download(config, data))


async def websocket(request, ws):
    print('opened websocket')
    CURRENT_WEBSOCKETS.append(ws)
    await handle_websocket(request.app.config, ws)


async def download(config, data):
    try:
        url = urlparse(data['value']).geturl()
        if not data['value'].endswith('.zip'):
            print('invalid file extension, expected .zip')
            del LINKS_SUBMITTED[data['id']]
            raise ValueError('invalid file extension, expected .zip')

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                filepath = join(TEMP_DIR, str(data['id']) + '.zip')
                with open(filepath, 'wb+') as f:
                    while True:
                        chunk = await resp.content.read(400)
                        if not chunk:
                            break
                        f.write(chunk)
        name = unzip(config, url, filepath)
        await asyncio.gather(*[notify_link_name(ws, data['id'], name) for ws in CURRENT_WEBSOCKETS])
    except Exception as exc:
        print(f'Exception:', exc)
        await asyncio.gather(*[notify_link_state(ws, data['id'], 'error') for ws in CURRENT_WEBSOCKETS])
        return

    await asyncio.gather(*[notify_link_state(ws, data['id'], 'complete') for ws in CURRENT_WEBSOCKETS])


def unzip(config, url, filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as zip:
            extract_dir = filepath[:-4]
            zip.extractall(extract_dir)
    finally:
        os.remove(filepath)

    with open(join(extract_dir, 'info.dat')) as f:
        info = json.load(f)

    song_name = info['_songSubName']
    song_id = url.split('/')[-2]
    new_folder_name = f'{song_id} {song_name}'

    move_path = join(config['CUSTOM_LEVELS_DIR'], new_folder_name)
    if os.path.exists(move_path):
        return new_folder_name

    shutil.move(extract_dir, join(config['CUSTOM_LEVELS_DIR'], new_folder_name))
    return new_folder_name
