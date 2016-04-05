#!/usr/bin/python

import os,sys,argparse
import json
import logging
import requests,urllib2,urllib
import time
from apiclient.discovery import build
from apiclient.errors import HttpError

import urlparse

import subprocess

from pycommons import generic_logging
generic_logging.init(level=logging.DEBUG)
logger = logging.getLogger('youtube')

class FileExistsException(Exception):
	pass
class FileLengthMismatchException(Exception):
	pass
class NoSearchResultException(Exception):
	pass
class YoutubeInMp3Exception(Exception):
	pass

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#	 https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = ""
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

import common

d = common.get_config()
DEVELOPER_KEY = d['DEVELOPER_KEY']

yt_playlist_info = {}

def build_youtube():
	return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
		developerKey=DEVELOPER_KEY)

def youtube_search(options):
	youtube = build_youtube()
	# Call the search.list method to retrieve results matching the specified
	# query term.
	try:
		search_response = youtube.search().list(
			q=options.artist + ' ' + options.track,
			part="id,snippet",
			order='viewCount',
			maxResults=options.max_results
		).execute()
	except Exception, e:
		logger.critical('Failed to perform youtube search: %s' % (e))
		raise e

	videos = []

	# Add each result to the appropriate list, and then display the lists of
	# matching videos, channels, and playlists.
	owner_whitelist = ['vevo', 'sony']
	keyword_blacklist = ['full album', 'album']

	for search_result in search_response.get("items", []):
		if search_result["id"]["kind"] == "youtube#video":
			info = search_result['snippet']
			for x in owner_whitelist:
				if x in info['channelTitle'].lower() and \
						options.track.lower() in info['title'].lower():
					videos.append(search_result)

	if len(videos) == 0:
		for search_result in search_response.get("items", []):
			if search_result["id"]["kind"] == "youtube#video":
				info = search_result['snippet']
				title = info['title'].lower()
				keywords = [options.artist, options.track]
				failed = False
				for word in keyword_blacklist:
					if word.lower() in title:
						failed = True
#				for word in keywords:
#					if word.lower() not in title:
#						failed = True
				if not failed:
					videos.append(search_result)

	for v in videos:
		logger.debug(json.dumps(v, indent=4))
	return videos

def get_playlist_videos(playlistId, **kwargs):
	def __get_playlist_videos(playlistId, **kwargs):
		youtube = build_youtube()
		try:
			response = youtube.playlistItems().list(playlistId=playlistId, **kwargs).execute()
			items = response['items']
			while response.get('nextPageToken', None):
				response = youtube.playlistItems().list(playlistId=playlistId, pageToken=response['nextPageToken'], **kwargs).execute()
				items.extend(response['items'])
		except Exception, e:
			logger.critical("Failed to obtain playlist videos for ID: %s" % (playlistId), exc_info=1)
			items = []
		return items
	if not kwargs.get('part', None):
		kwargs['part'] = "snippet"
	if not kwargs.get('maxResults', None):
		kwargs['maxResults'] = 50
	if not yt_playlist_info.get(playlistId, None):
		info = __get_playlist_videos(playlistId, **kwargs)
		if info and not yt_playlist_info.get(playlistId, None):
			yt_playlist_info[playlistId] = info
	else:
		info = yt_playlist_info[playlistId]
	return info

def create_youtube_url(id):
	return 'http://www.youtube.com/watch?v=%s' % (id)

def download(youtube_url, out, mp3):
	base_dir = os.path.abspath(os.path.dirname(__file__))
	youtube_dl = os.path.join(base_dir, 'youtube-dl')
	cmd = '%s %s -o "%s"' % (youtube_dl, youtube_url, out)
	if mp3:
		cmd += ' -x --audio-format "mp3"'
	logger.info(cmd)
	if os.path.exists(out):
		raise FileExistsException('File Exists!')
	p = subprocess.Popen(cmd, shell=True)
	p.wait()

def setup_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument("--artist", help="Search term", default="Taylor Swift")
	parser.add_argument("--track", help="Search term", default="Blank Space")
	parser.add_argument("--out", default='Blank Space - Taylor Swift.mp3',
			help="Output file")
	parser.add_argument("--max-results", help="Max results", default=5)
	parser.add_argument('--download', help='Download url', default=None)
	parser.add_argument('--playlist', action='store_true', default=False,
			help='Download playlist')
	parser.add_argument('--mp3', action='store_true', default=False,
			help='Download as MP3')
	return parser

def main(argv):
	parser = setup_parser()
	args = parser.parse_args(argv[1:])

	if args.download:
		if args.playlist:
			if os.path.isfile(args.out):
				os.remove(ags.out)
			if not os.path.exists(args.out):
				os.makedirs(args.out)
			if '://' in args.download:
				parts = urlparse.urlsplit(args.download)
				qs = urlparse.parse_qs(parts.query)
				playlist = get_playlist_videos(qs['list'][0])
			else:
				playlist = get_playlist_videos(args.download)
			for item in playlist:
				videoid = item['snippet']['resourceId']['videoId']
				out = os.path.join(args.out, item['snippet']['title'] + '.mp3')
				download(create_youtube_url(videoid), out, args.mp3)
		else:
			download(args.download, args.out, args.mp3)
		return

	try:
		results = youtube_search(args)
		if len(results) < 1:
			raise NoSearchResultException("Did not find any results for query string '%s %s'" % (args.artist, args.track))
		result = results[0]
		url = create_youtube_url(result['id']['videoId'])
		download(url, args.out, mp3=True)
	except HttpError, e:
		print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)


if __name__ == "__main__":
	main(sys.argv)
