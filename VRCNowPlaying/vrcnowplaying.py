"""
VRCNowPlaying - Show what you're listening to in your chatbox!
(c) 2022 CyberKitsune & MatchaCat
"""

from datetime import timedelta
import time
from pythonosc import udp_client
import asyncio

cutlet_installed = True
try:
    import cutlet
except ModuleNotFoundError as err:
    cutlet_installed = False

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionPlaybackStatus

katsu = None

if cutlet_installed:
    katsu = cutlet.Cutlet()
    katsu.use_foreign_spelling = False

async def get_media_info():
    sessions = await MediaManager.request_async()

    current_session = sessions.get_current_session()
    if current_session:  # there needs to be a media session running
        if True: # TODO: Media player selection
            info = await current_session.try_get_media_properties_async()

            # song_attr[0] != '_' ignores system attributes
            info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

            # converts winrt vector to list
            info_dict['genres'] = list(info_dict['genres'])

            pbinfo = current_session.get_playback_info()

            info_dict['status'] = pbinfo.playback_status

            tlprops = current_session.get_timeline_properties()

            if tlprops.end_time != timedelta(0):
                info_dict['pos'] = tlprops.position
                info_dict['end'] = tlprops.end_time

            return info_dict


    raise Exception("No media source running.")

def get_td_string(td):
    seconds = abs(int(td.seconds))

    minutes, seconds = divmod(seconds, 60)
    return '%i:%02i' % (minutes, seconds)

def main():
    global cutlet_installed
    print("VRCNowPlaying is now running")
    lastPaused = False
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    warnedMedia = False
    while True:
        try:
            current_media_info = asyncio.run(get_media_info()) # Fetches currently playing song for winsdk 
        except Exception as e:
            if not warnedMedia:
                print("!!!", e)
                warnedMedia = True
            continue

        warnedMedia = False

        song_artist, song_title = (current_media_info['artist'], current_media_info['title'])
        if not song_artist.isascii() and cutlet_installed:
            song_artist = katsu.romaji(song_artist)

        if not song_title.isascii() and cutlet_installed:
            song_title = katsu.romaji(song_title)

        posstr = ""

        if 'pos' in current_media_info:
            posstr = " <%s / %s>" % (get_td_string(current_media_info['pos']), get_td_string(current_media_info['end']))

        current_song_string = "( NP: %s - %s%s )" % (song_artist, song_title, posstr)

        if not current_song_string.isascii() and cutlet_installed:
            current_song_string = katsu.romaji(current_song_string)
        if len(current_song_string) >= 144 :
            current_song_string = current_song_string[:144]
        if current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            #print(current_song_string)
            client.send_message("/chatbox/input", [current_song_string.encode('ascii', errors="replace").decode(), True])
            lastPaused = False
        elif current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED and not lastPaused:
            client.send_message("/chatbox/input", ["( Playback Paused )", True])
            #print("( Playback Paused )")
            lastPaused = True
        time.sleep(1.5) # 1.5 sec delay to update with no flashing

if __name__ == "__main__":
    main()