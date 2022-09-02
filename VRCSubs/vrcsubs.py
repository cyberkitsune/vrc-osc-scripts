"""
VRCSubs - A script to create "subtitles" for yourself using the VRChat textbox!
(c) 2022 CyberKitsune & other contributors.
"""

import queue, threading, datetime, os, time, textwrap
import speech_recognition as sr
from speech_recognition import UnknownValueError, WaitTimeoutError, AudioData
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# I am typing enough characters that it should be truncated I GUESS I mean like 144 is great and all but who's afraid of the 138, trance music is really funny haha lmao

config = {'FollowMicMute': True, 'CapturedLanguage': "en-US"}
state = {'selfMuted': False}
state_lock = threading.Lock()

r = sr.Recognizer()
audio_queue = queue.Queue()

'''
STATE MANAGEMENT
This should be thread safe
'''
def get_state(key):
    global state, state_lock
    state_lock.acquire()
    result = None
    if key in state:
        result = state[key]
    state_lock.release()
    return result

def set_state(key, value):
    global state, state_lock
    state_lock.acquire()
    state[key] = value
    state_lock.release()

'''
SOUND PROCESSING THREAD
'''
def process_sound():
    global audio_queue, r, config
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    current_text = ""
    last_text = ""
    last_disp_time = datetime.datetime.now()
    print("[ProcessThread] Starting audio processing!")
    while True:
        ad, final = audio_queue.get()
        client.send_message("/chatbox/typing", (not final))
        text = None
        if config["FollowMicMute"] and get_state("selfMuted"):
            continue
        try:
            #client.send_message("/chatbox/typing", True)
            text = r.recognize_google(ad, language=config["CapturedLanguage"])
        except UnknownValueError:
            #client.send_message("/chatbox/typing", False)
            continue
        except TimeoutError:
            #client.send_message("/chatbox/typing", False)
            print("[ProcessThread] Timeout Error when recognizing speech!")
            continue
        except Exception as e:
            print("[ProcessThread] Exception!", e)
            #client.send_message("/chatbox/typing", False)
            continue

        time_now = datetime.datetime.now()
        difference = time_now - last_disp_time
        current_text = text

        if last_text == current_text:
            continue

        last_text = current_text

        diff_in_milliseconds = difference.total_seconds() * 1000
        if diff_in_milliseconds < 1500:
            ms_to_sleep = 1500 - diff_in_milliseconds
            print("[ProcessThread] Sending too many messages! Delaying by", (ms_to_sleep / 1000.0), "sec to not hit rate limit!")
            time.sleep(ms_to_sleep / 1000.0)

        if len(current_text) > 144:
            current_text = textwrap.wrap(current_text, width=144)[-1]

        last_disp_time = datetime.datetime.now()
        
        client.send_message("/chatbox/input", [current_text, True])
        print("[ProcessThread] Recognized:",current_text)

'''
AUDIO COLLECTION THREAD
'''
def collect_audio():
    global audio_queue, r, config
    mic = sr.Microphone()
    print("[AudioThread] Starting audio collection!")
    did = mic.get_pyaudio().PyAudio().get_default_input_device_info()
    print("[AudioThread] Using", did.get('name'), "as Microphone!")
    with mic as source:
        audio_buf = None
        while True:
            audio = None
            try:
                audio = r.listen(source, phrase_time_limit=2, timeout=0.3)
            except WaitTimeoutError:
                if audio_buf is not None:
                    audio_queue.put((audio_buf, True))
                    audio_buf = None
                continue

            if audio is not None:
                if audio_buf is None:
                    audio_buf = audio
                else:
                    audio_buf = AudioData(audio_buf.frame_data + audio.frame_data, audio.sample_rate, audio.sample_width)
                audio_queue.put((audio_buf, False))

'''
OSC BLOCK
TODO: This maybe should be bundled into a class
'''
class OSCServer():
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self._def_osc_dispatch)
        self.dispatcher.map("/avatar/parameters/MuteSelf", self._osc_muteself)

        self.server = BlockingOSCUDPServer(("127.0.0.1", 9001), self.dispatcher)
        self.server_thread = threading.Thread(target=self._process_osc)

    def launch(self):
        self.server_thread.start()

    def shutdown(self):
        self.server.shutdown()
        self.server_thread.join()

    def _osc_muteself(self, address, *args):
        print("[OSCThread] Mute is now", args[0])
        set_state("selfMuted", args[0])

    def _def_osc_dispatch(self, address, *args):
        pass
        #print(f"{address}: {args}")

    def _process_osc(self):
        print("[OSCThread] Launching OSC server thread!")
        self.server.serve_forever()


'''
MAIN ROUTINE
'''
def main():
    global config
    # Load config
    cfgfile = f"{os.path.dirname(os.path.realpath(__file__))}/Config.yml"
    if os.path.exists(cfgfile):
        print("[VRCSubs] Loading config from", cfgfile)
        with open(cfgfile, 'r') as f:
            config = load(f, Loader=Loader)

    # Start threads
    pst = threading.Thread(target=process_sound)
    pst.start()

    cat = threading.Thread(target=collect_audio)
    cat.start()
    
    osc = None
    if config['FollowMicMute']:
        print("[VRCSubs] FollowMicMute is enabled in the config, speech recognition will pause when your mic is muted ingame!")
        osc = OSCServer()
        osc.launch()
    else:
        print("[VRCSubs] FollowMicMute is NOT enabled in the config, speech recognition will work even while muted ingame!")

    pst.join()
    cat.join()
    
    if osc is not None:
        osc.shutdown()

if __name__ == "__main__":
    main()