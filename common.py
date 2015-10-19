import os,sys,argparse
import json

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

def get_config(config_path=CONFIG_FILE_PATH):
	if not os.path.exists(config_path):
		logger.critical("File '%s' does not exist! Creating template ... " \
				"Please update template with values" % (config_path))
		create_config_file()
		sys.exit(-1)
	else:
		d = None
		with open(config_path, 'rb') as f:
			d = json.loads(f.read())
		for key in CONFIG_KEYS:
			assert d.get(key, None), "Key '%s' does not exist in config file" % (key)

		# Now set the variables
		return d


