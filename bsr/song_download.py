import logging
import os
import shutil
import zipfile
from os.path import join
from urllib.parse import urlparse

import aiohttp
import simplejson as json

log = logging.getLogger(__name__)


def _get_song_id(data):
    value = str(data['value'])
    if 0 < len(value) <= 5:
        # Assume value is the song_id
        return value

    url = urlparse(value)
    if url.scheme == 'beatsaver':
        return url.netloc
    elif url.scheme == 'https':
        if url.path.endswith('.zip'):
            # Assume url is /cdn/<song_id>/<uuid>.zip
            return url.path.rsplit('/', 2)[1]
        return url.path.split('/')[-1]

    raise ValueError(f'cannot parse url from value {value}')


async def _download_to_tmp_dir(config, data, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            filepath = join(config['temp_dir'], str(data['id']) + '.zip')
            with open(filepath, 'wb+') as f:
                while True:
                    chunk = await resp.content.read(400)
                    if not chunk:
                        break
                    f.write(chunk)
    return filepath


def _unzip(song_id, filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as zip:
            old_folder = filepath[:-4]
            zip.extractall(old_folder)
    finally:
        os.remove(filepath)

    with open(join(old_folder, 'info.dat')) as f:
        info = json.load(f)

    song_name = info['_songName']
    new_folder = f'{song_id} ({song_name.strip()})'
    return old_folder, new_folder


def _move_tmp_to_beastsaber(config, tmp_dir_folder, song_folder_name):
    move_path = join(config['custom_levels_dir'], song_folder_name)
    if os.path.exists(move_path):
        return song_folder_name
    shutil.move(tmp_dir_folder, move_path)


async def download(config, data):
    song_id = _get_song_id(data)
    url = config['bsaber_download_url'].format(song_id)

    log.info(f'downloading {url}...')
    filepath = await _download_to_tmp_dir(config, data, url)
    log.info(f'saved to {filepath}')
    old_folder, new_folder = _unzip(song_id, filepath)
    log.info(f'moving {old_folder} to {new_folder}')
    _move_tmp_to_beastsaber(config, old_folder, new_folder)
    log.info('done')
    return new_folder
