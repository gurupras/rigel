import os,sys,argparse
import json
import shlex

from unidecode import unidecode

import logging
from pycommons import generic_logging
generic_logging.init(level=logging.INFO)
logger = logging.getLogger('spotify_downloader')

import youtube
from spotify import Spotify

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILE = '.config'
CONFIG_FILE_PATH = os.path.join(BASE_DIR, CONFIG_FILE)

CONFIG_KEYS = [
	'TOKENS_FILE',
	'DEVELOPER_KEY',
]

def create_config_file():
	d = {'TOKENS_FILE' : '.tokens'}
	for entry in CONFIG_KEYS:
		if d.get(entry, None) is None:
			d[entry] = ''

	with open(CONFIG_FILE_PATH, 'wb') as f:
		f.write(json.dumps(d, indent=4))

if not os.path.exists(CONFIG_FILE_PATH):
	logger.critical("File '%s' does not exist! Creating template ... " \
			"Please update template with values")
	create_config_file()
	sys.exit(-1)
else:
	d = None
	with open(CONFIG_FILE_PATH, 'rb') as f:
		d = json.loads(f.read())
	for key in CONFIG_KEYS:
		assert d.get(key, None), "Key '%s' does not exist in config file" % (key)

	# Now set the variables
	Spotify.TOKENS_FILE = d['TOKENS_FILE']
	youtube.DEVELOPER_KEY = d['DEVELOPER_KEY']

def setup_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('--out', default='out')
	return parser

def to_ascii(string):
	return unidecode(string)

def main(argv):
	parser = setup_parser()
	args = parser.parse_args(argv[1:])

	spotify = Spotify()
	spotify.authenticate()

	if not os.path.exists(args.out):
		os.makedirs(args.out)

	for track_list in spotify.get_user_tracks():
		for track in track_list['items']:
			track = track['track']
			artist = None
			title = None
			try:
				artist = to_ascii(track['artists'][0]['name'].encode('utf-8'))
				title = to_ascii(track['name'].encode('utf-8'))
				assert artist and title
			except Exception, e:
				logger.critical('FAIL/%s\n - %s', json.dumps(track, indent=4), e)
				raise e
				print json.dumps(track, indent=4)
				sys.exit(-1)

			name = '%s - %s.mp3' % (title, artist)
			out = os.path.join(args.out, '%s' % (name))
			try:
				cmdline = 'youtube.py --artist="%s" --track="%s" --out="%s"' % (artist, title, out)
				logger.debug('Downloading %s' % (out))
				youtube.main(shlex.split(cmdline))
				logger.info('OK/%s' % (name))
			except youtube.FileExistsException, e:
				logger.info('SKIP/%s - %s', name, e)
			except youtube.NoSearchResultException, e:
				logger.critical('FAIL/%s - %s', name, e)
			except youtube.FileLengthMismatchException, e:
				logger.warn('SKIP/%s - %s', name, e)
			except Exception, e:
				logger.critical('FAIL/%s - %s', name, e)


if __name__ == '__main__':
	main(sys.argv)
