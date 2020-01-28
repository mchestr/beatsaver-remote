import argparse
import logging
import os
import sys
from os.path import join

from sanic import Sanic
from sanic_cors import CORS


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger('bsr')
    logger.addHandler(handler)


def main():
    parser = argparse.ArgumentParser('BeatSaverRemote')
    parser.add_argument('beatsaber_dir', help='Path to BeatSaber Directory')
    parser.add_argument('--tmp-dir', help='Path to temp directory', default='./temp')
    parser.add_argument('--bsaber-download-url', help='bsaber URL to song_id download',
                        default='https://beatsaver.com/api/download/key/{}')
    args = parser.parse_args()

    from bsr.app import blueprint, websocket

    app = Sanic()
    app.blueprint(blueprint)
    app.add_websocket_route(websocket, '/ws')
    CORS(app)

    bsr_config = {
        'beatsaber_dir': args.beatsaber_dir,
        'bsaber_download_url': args.bsaber_download_url,
        'custom_levels_dir': join(args.beatsaber_dir, 'Beat Saber_Data', 'CustomLevels'),
        'temp_dir': args.tmp_dir,
    }

    try:
        os.mkdir(bsr_config['temp_dir'])
    except IOError:
        pass

    app.config.bsr = bsr_config
    app.run('0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
