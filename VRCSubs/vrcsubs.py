"""
VRCSubs - A script to create "subtitles" for yourself using the VRChat textbox!
(c) 2022 CyberKitsune & other contributors.
"""

import queue, threading, datetime, os
import speech_recognition as sr
from speech_recognition import UnknownValueError, WaitTimeoutError
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


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
    last_disp_time = datetime.datetime.now()
    print("Starting audio processing!")
    while True:
        ai = audio_queue.get()
        text = None
        try:
            client.send_message("/chatbox/typing", True)
            text = r.recognize_google(ai, language=config["CapturedLanguage"])
        except UnknownValueError:
            client.send_message("/chatbox/typing", False)
            continue
        except TimeoutError:
            client.send_message("/chatbox/typing", False)
            client.send_message("/chatbox/input", ["[Timeout Error]", True])
            print("Timeout Error when recognizing speech!")
            continue
        except Exception as e:
            print("Exception!", e)
            client.send_message("/chatbox/typing", False)
            continue
        
        time_now = datetime.datetime.now()
        difference = time_now - last_disp_time
        if difference.seconds < 3:
            current_text = current_text + " " + text
        else:
            current_text = text

        last_disp_time = datetime.datetime.now()
        client.send_message("/chatbox/typing", False)
        client.send_message("/chatbox/input", [current_text, True])
        print(current_text)

'''
AUDIO COLLECTION THREAD
'''
def collect_audio():
    global audio_queue, r, config
    mic = sr.Microphone()
    print("Starting audio collection!")
    with mic as source:
        while True:
            if config["FollowMicMute"] and get_state("selfMuted"):
                continue
            audio = None
            try:
                audio = r.listen(source, phrase_time_limit=3, timeout=1)
            except WaitTimeoutError:
                continue

            if audio is not None:
                audio_queue.put(audio)

'''
OSC BLOCK
TODO: This maybe should be bundled into a class
'''
def _osc_muteself(address, *args):
    print("Mute state", args[0])
    set_state("selfMuted", args[0])

def _def_osc_dispatch(address, *args):
    pass
    #print(f"{address}: {args}")

def process_osc():
    print("Launching OSC server thread!")
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(_def_osc_dispatch)
    dispatcher.map("/avatar/parameters/MuteSelf", _osc_muteself)

    server = BlockingOSCUDPServer(("127.0.0.1", 9001), dispatcher)
    server.serve_forever()


'''
MAIN ROUTINE
'''
def main():
    global config
    # Load config
    cfgfile = f"{os.path.dirname(os.path.realpath(__file__))}/Config.yml"
    if os.path.exists(cfgfile):
        print("Loading config from ", cfgfile)
        with open(cfgfile, 'r') as f:
            config = load(f, Loader=Loader)

    # Start threads
    pst = threading.Thread(target=process_sound)
    pst.start()

    cat = threading.Thread(target=collect_audio)
    cat.start()
    
    osc = threading.Thread(target=process_osc)
    osc.start()

    pst.join()
    cat.join()
    osc.join()

if __name__ == "__main__":
    main()