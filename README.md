# BeatSaber Remote

I created this to allow other people in the room to submit links to automatically download songs submitted to it.
The setup I have at home is awkward to manage on the TV, so this allows me to be lazy and have other people in the room
find songs they want to play and submit links which will automatically be downloaded.

## Setup

_Requires Python3.6+_

1. Run `npm run build` in the `./web` directory
2. Run `python -m venv venv && venv\Scripts\pip.exe install .`
3. Run the server ` venv\Scripts\python.exe -m bsr run "<path to beatsaber installation>"`
4. Visit `http://localhost:8000`

## Usage

Have visitors on your local network visit your hosts IP, then submit links from bsaber website and profit!

## Disclaimer

Don't run this on untrusted networks as there is no authentication or authorization, and the app can 
modify your filesystem. Use at your own risk.

## License

MIT
