#!/usr/bin/python

import os,sys,argparse
import json
import logging
import requests,urllib2,urllib
import time
from apiclient.discovery import build
from apiclient.errors import HttpError

import subprocess

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

def youtube_search(options):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
		developerKey=DEVELOPER_KEY)

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

def create_youtube_url(id):
	return 'http://www.youtube.com/watch?v=%s' % (id)

def download(youtube_url, out):
	base_dir = os.path.abspath(os.path.dirname(__file__))
	youtube_dl = os.path.join(base_dir, 'youtube-dl')
	cmd = '%s %s -x -o "%s" --audio-format "mp3"' % (youtube_dl, youtube_url, out)
	logger.info(cmd)
	if os.path.exists(out):
		raise FileExistsException('File Exists!')
	p = subprocess.Popen(cmd, shell=True)
	p.wait()

def setup_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument("--artist", help="Search term", default="Taylor Swift")
	parser.add_argument("--track", help="Search term", default="Blank Space")
	parser.add_argument("--out", help="Output file", default='Blank Space - Taylor Swift.mp3')
	parser.add_argument("--max-results", help="Max results", default=5)
	return parser

def main(argv):
	parser = setup_parser()
	args = parser.parse_args(argv[1:])

	try:
		results = youtube_search(args)
		if len(results) < 1:
			raise NoSearchResultException("Did not find any results for query string '%s %s'" % (args.artist, args.track))
		result = results[0]
		url = create_youtube_url(result['id']['videoId'])
		download(url, args.out)
	except HttpError, e:
		print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)


if __name__ == "__main__":
	main(sys.argv)
