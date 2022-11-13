"""
VRCNowPlaying - Show what you're listening to in your chatbox!
(c) 2022 CyberKitsune & MatchaCat
"""

from datetime import timedelta
import time, os, threading, traceback
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import asyncio

from tinyoscquery.queryservice import OSCQueryService
from tinyoscquery.utility import get_open_tcp_port, get_open_udp_port

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


config = {'DisplayFormat': "( NP: {song_artist} - {song_title}{song_position} )", 'PausedFormat': "( Playback Paused )"}

last_displayed_song = ("","")

# TODO Maybe add a timeout override...
pause_update = False

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

def osc_update_status(address, *args):
    global pause_update
    pause_update = args[0]
    print("[OSCControl] Remote sent pause update:", pause_update)

def osc_input_thread():
    global pause_update
    osc_port = get_open_udp_port()
    oscjson_port = get_open_tcp_port()
    oscqs = OSCQueryService("VRCNowPlaying", oscjson_port, osc_port)
    oscqs.advertise_endpoint("/textcontrol/pause", pause_update)
    dispatcher = Dispatcher()
    dispatcher.map("/textcontrol/pause", osc_update_status)
    server = BlockingOSCUDPServer(("127.0.0.1", osc_port), dispatcher)
    print("[OSCControl] OSC Control server starting...")

    server.serve_forever()



def main():
    global config, last_displayed_song, pause_update
    # Load config
    cfgfile = f"{os.path.dirname(os.path.realpath(__file__))}/Config.yml"
    if os.path.exists(cfgfile):
        print("[VRCSubs] Loading config from", cfgfile)
        with open(cfgfile, 'r', encoding='utf-8') as f:
            config = load(f, Loader=Loader)
    osc_thread = threading.Thread(target=osc_input_thread)
    osc_thread.start()
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

        if 'pos' in current_media_info:
            song_position = " <%s / %s>" % (get_td_string(current_media_info['pos']), get_td_string(current_media_info['end']))

        current_song_string = config['DisplayFormat'].format(song_artist=song_artist, song_title=song_title, song_position=song_position)

        if len(current_song_string) >= 144 :
            current_song_string = current_song_string[:144]
        if current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            if last_displayed_song != (song_artist, song_title):
                last_displayed_song = (song_artist, song_title)
                print("[VRCNowPlaying]", current_song_string)
            if not pause_update:
                client.send_message("/chatbox/input", [current_song_string, True])
            lastPaused = False
        elif current_media_info['status'] == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED and not lastPaused:
            if not pause_update:
                client.send_message("/chatbox/input", [config['PausedFormat'], True])
                print("[VRCNowPlaying]", config['PausedFormat'])
            last_displayed_song = ("", "")
            lastPaused = True
        time.sleep(1.5) # 1.5 sec delay to update with no flashing

    osc_thread.join()

if __name__ == "__main__":
    main()