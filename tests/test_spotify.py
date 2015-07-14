import os,sys
import requests, json
import unittest

__tests_dir = os.path.dirname(os.path.abspath(__file__))
__base_dir = os.path.join(__tests_dir, '..')
sys.path.insert(1, __base_dir)

from spotify import Spotify


class SpotifyTest(unittest.TestCase):

	def setup(self):
		self.spotify = Spotify()
		self.spotify.authenticate()

	def test_constructor(self):
		Spotify()
	
	def test_authenticate(self):
		self.setup()

	def test_whoami(self):
		self.setup()
		user = self.spotify.whoami()
	
	def test_get_user_playlists(self):
		self.setup()
		user = self.spotify.whoami()
		self.spotify.get_user_playlists(user)
	
	def test_get_user_tracks(self):
		self.setup()
		user = self.spotify.whoami()
		self.spotify.get_user_tracks(user)

if __name__ == '__main__':
	unittest.main()
