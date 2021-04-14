import json
import time
import spotipy 
import difflib
from pprint import pprint as _pprint

from spotipy.oauth2 import SpotifyClientCredentials


from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from auth import login_required
from db import get_db

bp = Blueprint('playlist', __name__)

client_credentials_manager = SpotifyClientCredentials('f46fa1edd57a49ddb23b635983381176', client_secret='75155ac36a514896a1588a7bf18c07f6')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

@bp.route('/', methods=('GET', 'POST'))
@login_required
def home():
    
    if request.method == 'POST':
        name = request.form['spotifyName']
        playlistID = request.form['playlistID']
        error = None
        
       
        if error is None:
            return redirect(url_for('playlist.playlistView', name=name,playlistID=playlistID))

        flash(error)


    return render_template('playlist/home.html')


@bp.route('/playlistView/<name>/<playlistID>')
@login_required
def playlistView(name, playlistID):
    
    track_ids = get_track_ids(name, playlistID)

    print(len(track_ids))
    '''
    print(track_ids)'''
    db = get_db()
    tracks = []
    for i in range(len(track_ids)):
    
        track = get_track_data(track_ids[i])
        tracks.append(track)
        tracks.append('***@TRACKSPLITTER@***')

    with open('spotify-data.json', 'w') as outfile:
        json.dump(tracks, outfile, indent=4)

    db.execute(
        'INSERT INTO playlist (spotify_id, track_info, user_id, title) VALUES (?, ?, ?, ?)',
        (playlistID, json.dumps(tracks), g.user['id'], 'n/a')
    )
    db.commit()
    
    return render_template('playlist/playlistView.html', spotifyName=name, playlist=playlistID, tracks=tracks)

@bp.route('/about')
def about():
    
    return render_template('about.html')

    
@bp.route('/playlists')
@login_required
def playlistsView():
    int = g.user['id']
    db = get_db()
    playlists = db.execute(
        'SELECT spotify_id FROM playlist WHERE user_id = ? group by spotify_id',
        (g.user['id'],)
    ).fetchall()
    return render_template('playlist/playlistsView.html', playlists=playlists)

@bp.route('/<name>/<playlistID>/records', methods=('GET', 'POST'))
@login_required
def RecordsView(name, playlistID):
    if request.method == 'POST':
        chosen = request.form.getlist('chosen')
        print(chosen)
        db = get_db()

        record1 = db.execute(
            'SELECT track_info FROM playlist WHERE id = ?',
            (chosen[0],)
        ).fetchone()

        record2 = db.execute(
            'SELECT track_info FROM playlist WHERE id = ?',
            (chosen[1],)
        ).fetchone()
        return render_template('playlist/compareView.html', report=Compare(record1[0], record2[0]))
        


    
    db = get_db()
    records = db.execute(
        'SELECT created, id FROM playlist WHERE user_id = ? AND spotify_id = ?',
        (g.user['id'], playlistID)
    ).fetchall()
    
    return render_template('playlist/recordsView.html', spotifyName=name, records=records, playlistID = playlistID)

def Compare(record1, record2):
    
    
    record1Split = record1.split('***@TRACKSPLITTER@***')
    record2Split = record2.split('***@TRACKSPLITTER@***')
    d = difflib.Differ()
    
    record1Split.pop(0)
    record2Split.pop(0)
    record1Split.pop(len(record1Split)-1)
    record2Split.pop(len(record2Split)-1)

    result = list(d.compare(record1Split, record2Split))
    result.sort(reverse=True)




    _pprint(result)
    return result


@bp.route('/<name>/<playlistID>/<id>')
@login_required
def RecordView(name, playlistID, id):
    
    db = get_db()
    record = db.execute(
        'SELECT track_info FROM playlist WHERE user_id = ? AND id = ?',
        (g.user['id'], id)
    ).fetchall()
    
    return render_template('playlist/recordView.html', spotifyName=name, record=record)


@bp.route('/<name>/<playlistID1>/<playlistID2>')
@login_required
def CompareView(name, playlistID, id):
    
    
    

    return render_template('playlist/recordView.html', spotifyName=name, record=record)


def get_track_ids(name, playlist_id):
    results = sp.user_playlist_tracks(name,playlist_id)
    
    '''playListName = results['name']
    '''
    
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    music_id_list = []
    for item in tracks:
        music_track = item['track']
        music_id_list.append(music_track['id'])
    return music_id_list


def get_track_data(track_id):
    print(track_id)
    if track_id is not None:
        meta = sp.track(track_id)
        track_details = {"name": meta['name'], "album": meta['album']['name'], 
                        "artist": meta['album']['artists'][0]['name'],
                        "release_date": meta['album']['release_date'],
                        "duration_in_mins": round((meta['duration_ms'] * 0.001) / 60.0, 2)}
        return track_details
    
    return 'local track'