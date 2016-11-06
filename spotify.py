import os
import requests, json
import urlparse
import urllib
import base64
import logging

logger = logging.getLogger('spotify')

_base_dir = os.path.dirname(os.path.abspath(__file__))

class AuthenticationException(Exception):
	pass

class Spotify:
	TOKENS_FILE=os.path.join(_base_dir, '.tokens')
	redirect_uri = 'http://localhost:8888'

	REFRESH_TOKEN_STRING = 'refresh_token'

	# URLs
	AUTH_URL  = 'https://accounts.spotify.com/authorize'
	TOKEN_URL = 'https://accounts.spotify.com/api/token'
	SELF_URL  = 'https://api.spotify.com/v1/me'
	USER_BASE_URL  = 'https://api.spotify.com/v1/users/'
	AUDIO_ANALYSIS_URL = 'https://api.spotify.com/v1/audio-analysis/'
	AUDIO_FEATURES_URL = 'https://api.spotify.com/v1/audio-features/'
	SEARCH_URL = 'https://api.spotify.com/v1/search'

	def __init__(self):
		assert os.path.exists(Spotify.TOKENS_FILE), 'Please create .tokens file with client_id and client_secret keys'
		self.tokens = dict(self.load_tokens())
		self.update_tokens(self.tokens)
		self.base64 = base64.b64encode(self.client_id + ':' + self.client_secret)

	def initiate_authorization(self):
		params = {
				'client_id' : self.client_id,
				'response_type' : 'code',
				'redirect_uri' : self.redirect_uri,
				'scope' : 'user-library-read user-library-modify',
		}
		r = requests.get(self.AUTH_URL, params=params)
		if not r.status_code == requests.codes.ok:
			raise AuthenticationException('Failed to obtain authorization code')

		logger.info('Open: %s' % (r.url))
		query_str = urlparse.urlparse(raw_input('Enter url:'))[4]
		code = urlparse.parse_qs(query_str)['code'][0]

		# Now get tokens
		params = {
				'grant_type' : 'authorization_code',
				'code' : code,
				'redirect_uri' : self.redirect_uri,
		}
		headers = self.get_token_request_headers()
		r = requests.post(self.TOKEN_URL, data=params, headers=headers)
		if not r.status_code == requests.codes.ok:
			raise AuthenticationException('Failed to obtain tokens')

		self.update_tokens(r.json())
		self.dump_tokens()


	def dump_tokens(self):
		with open(Spotify.TOKENS_FILE, 'wb') as f:
			f.write(json.dumps(self.tokens))


	def load_tokens(self):
		with open(Spotify.TOKENS_FILE, 'rbU') as f:
			return json.loads(f.read())


	def update_tokens(self, data):
		for key, value in dict(data).iteritems():
			setattr(self, key, value)
			self.tokens[key] = value


	def authenticate(self):
		if self.tokens.get('refresh_token', None) is None:
			self.initiate_authorization()
		else:
			params = {
					'grant_type' : self.REFRESH_TOKEN_STRING,
					'refresh_token' : self.refresh_token,
			}
			headers = self.get_token_request_headers()
			r = requests.post(self.TOKEN_URL, data=params, headers=headers)

			if not r.status_code == requests.codes.ok:
				logger.critical(r.json())
				raise AuthenticationException('Failed to obtain refresh token')
			self.update_tokens(r.json())
			if dict(r.json()).get(self.REFRESH_TOKEN_STRING, None):
				self.update_tokens(r.json())
				self.dump_tokens()


	def get_token_request_headers(self):
		headers = {
				'Authorization' : 'Basic %s' % (self.base64),
		}
		return headers

	def get_request_headers(self):
		headers = {
				'Authorization' : 'Bearer %s' % (self.access_token),
		}
		return headers

	def make_get_request(self, url, payload={}):
		headers = self.get_request_headers()
		r = requests.get(url, headers=headers, params=payload)
		if r.status_code is not requests.codes.ok:
			logger.critical(r.json())
			raise Exception('Failed to make get_request')
		return r.json()

	def whoami(self):
		result = self.make_get_request(self.SELF_URL)
		return User(result)

	def get_user_playlists(self, user=None):
		if not user:
			user = self.whoami()
		url = urlparse.urljoin(self.USER_BASE_URL, '%s/playlists' % (user))
		return self.return_generator(url)

	def get_user_tracks(self, user=None):
		if not user:
			user = self.whoami()
		url = urlparse.urljoin(self.USER_BASE_URL, '%s/tracks' % (user))
		return self.return_generator(url)

	def get_user_playlist_tracks(self, user=None, playlist=None):
		if not user:
			user = self.whoami()
		for result in self.get_user_playlists(user):
			for plist in result['items']:
				if playlist and plist['name'] != playlist:
					continue
				tracks_url = plist['tracks']['href']
				for track_list in self.return_generator(tracks_url):
					yield track_list

	def search(self, parameters):
		url = self.SEARCH_URL
		return self.make_get_request(url, parameters)

	def audio_analysis(self, trackid):
		url = urlparse.urljoin(self.AUDIO_ANALYSIS_URL, trackid)
		return self.make_get_request(url)

	def audio_features(self, trackid):
		url = urlparse.urljoin(self.AUDIO_FEATURES_URL, trackid)
		return self.make_get_request(url)




	def return_generator(self, url):
		req = {'next':url}
		while req['next']:
			req = self.make_get_request(req['next'])
			yield req


class User(dict):

	def __init__(self, json_data):
		super(User, self).__init__(json_data)

	def __repr__(self):
		return self.get('id', None)

def generate_tokens_file(**kwargs):
	with open('.tokens', 'wb') as f:
		f.write(json.dumps(kwargs))

