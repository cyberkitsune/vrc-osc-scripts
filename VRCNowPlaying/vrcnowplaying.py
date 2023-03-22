"""
VRCNowPlaying - Show what you're listening to in your chatbox!
(c) 2022 CyberKitsune & MatchaCat
"""

from datetime import timedelta
import time, os
import traceback
from pythonosc import udp_client
import asyncio

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionPlaybackStatus


class NoMediaRunningException(Exception):
    pass


config = {'DisplayFormat': "( NP: {song_artist} - {song_title}{song_position} )", 'PausedFormat': "( Playback Paused )", 'OnlyShowOnChange': False}

last_displayed_song = ("","")
displayed_timestamp = None
last_reported_timestamp = None

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
    else:
        raise NoMediaRunningException("No media source running.")

def get_td_string(td):
    seconds = abs(int(td.seconds))

    minutes, seconds = divmod(seconds, 60)
    return '%i:%02i' % (minutes, seconds)

def main():
    global config, last_displayed_song, displayed_timestamp, last_reported_timestamp
    # Load config
    cfgfile = f"{os.path.dirname(os.path.realpath(__file__))}/Config.yml"
    if os.path.exists(cfgfile):
        print("[VRCSubs] Loading config from", cfgfile)
        with open(cfgfile, 'r', encoding='utf-8') as f:
            new_config = load(f, Loader=Loader)
            if new_config is not None:
                for key in new_config:
                    config[key] = new_config[key]
    print("[VRCNowPlaying] VRCNowPlaying is now running")
    lastPaused = False
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    while True:
        try:
            current_media_info = asyncio.run(get_media_info()) # Fetches currently playing song for winsdk 
        except NoMediaRunningException:
            time.sleep(1.5)
            continue
        except Exception as e:
            print("!!!", e, traceback.format_exc())
            time.sleep(1.5)
            continue


        song_artist, song_title = (current_media_info['artist'], current_media_info['title'])

        song_position = ""

        if 'pos' in current_media_info \
        and current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            if current_media_info['end'].seconds == 50400:
                # FIXME: YouTube Live streams always report an end time of 50400 seconds. Using this for live detection.
                #        is there a better way...?

                song_position = " <LIVE>"
            else:
                if displayed_timestamp is None:
                    displayed_timestamp = current_media_info['pos']

                if last_reported_timestamp == current_media_info['pos']:
                    # 1.5 sec ago is the same as now. Add 1.5s
                    displayed_timestamp = displayed_timestamp + timedelta(seconds=1.5)
                else:
                    # Last reported is different then current. Use current info
                    last_reported_timestamp = current_media_info['pos']
                    displayed_timestamp = current_media_info['pos']
                    
                song_position = " <%s / %s>" % (get_td_string(displayed_timestamp), get_td_string(current_media_info['end']))

        current_song_string = config['DisplayFormat'].format(song_artist=song_artist, song_title=song_title, song_position=song_position)

        if len(current_song_string) >= 144 :
            current_song_string = current_song_string[:144]
        if current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            send_to_vrc = not config['OnlyShowOnChange']
            if last_displayed_song != (song_artist, song_title):
                send_to_vrc = True
                last_displayed_song = (song_artist, song_title)
                print("[VRCNowPlaying]", current_song_string)
            if send_to_vrc:
                client.send_message("/chatbox/input", [current_song_string, True, False])
            lastPaused = False
        elif current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED and not lastPaused:
            client.send_message("/chatbox/input", [config['PausedFormat'], True, False])
            print("[VRCNowPlaying]", config['PausedFormat'])
            last_displayed_song = ("", "")
            lastPaused = True
        time.sleep(1.5) # 1.5 sec delay to update with no flashing

if __name__ == "__main__":
    main()