# rigel
Ever been frustrated with Spotify not allowing you to play the songs you want on your smartphone?
With rigel you can access your Spotify playlist and use the information to download the tracks via Youtube.

# Installation
Setup virtualenv if necessary:  
    `virtualenv env --no-site-packages`  
    `source env/bin/activate`
    
Run pip:  
    `pip install -r requirements.txt`

Currently, there is no server to bounce authorization off of and so, you are required to get a client id and secret from Spotify.
Go to [Spotify](https://developers.spotify.com) and enable developer API
Add your client key and client secret to `.tokens` in JSON format  
`{"client_id": "", "client_secret": ""}`

Now, head over to [Google](https://console.developers.google.com/) and create credentials for API access of type Browser.

Run `python spotify_downloader.py` which should generate a `.config` file.  
Fill in the developer key you just created in this file.

Go ahead and run `python spotify_downloader.py` to download songs in your Spotify's 'Your Music'
