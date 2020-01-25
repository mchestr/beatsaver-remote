import sys

from bsr.app import new

if len(sys.argv) < 3:
    raise ValueError('must provide path to beatsaber installation as argument')

app = new(*sys.argv[2:])
app.run('0.0.0.0', port=8000)
