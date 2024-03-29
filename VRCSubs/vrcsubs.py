"""
VRCSubs - A script to create "subtitles" for yourself using the VRChat textbox!
(c) 2022 CyberKitsune & other contributors.
"""

import queue, threading, datetime, os, time, textwrap
import speech_recognition as sr
import translators
from tinyoscquery.queryservice import OSCQueryService, OSCAccess
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
from tinyoscquery.utility import get_open_tcp_port, get_open_udp_port


from speech_recognition import UnknownValueError, WaitTimeoutError, AudioData
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


config = {
    'FollowMicMute': True, 
    'CapturedLanguage': "en-US", 
    'TranscriptionMethod': "Google", 
    'TranscriptionRateLimit': 1200,
    'EnableTranslation': False, 
    'TranslateMethod': "Google", 
    'TranslateToken': "", 
    "TranslateTo": "en-US", 
    'AllowOSCControl': True, 
    'Pause': False, 
    'TranslateInterumResults': True,
    }
state = {'selfMuted': False}
state_lock = threading.Lock()

r = sr.Recognizer()
audio_queue = queue.Queue()

methods = {"Google": r.recognize_google, "Vosk": r.recognize_vosk}

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
    global audio_queue, r, config, methods
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    current_text = ""
    last_text = ""
    last_disp_time = datetime.datetime.now()
    translator = None
    
    print("[ProcessThread] Starting audio processing!")
    while True:
        if config["EnableTranslation"] and translator is None:
            tclass = None
            print("[ProcessThread] Enabling Translation!")
            if config["TranslateMethod"] in translators.registered_translators:
                tclass = translators.registered_translators[config["TranslateMethod"]]
            targs = config["TranslateToken"]

            try:
                translator = tclass(targs)
            except Exception as e:
                print("[ProcessThread] Unable to initalize translator!", e)
            
        
        ad, final = audio_queue.get()

        if config["FollowMicMute"] and get_state("selfMuted"):
            continue

        if config["Pause"]:
            continue

        client.send_message("/chatbox/typing", (not final))

        if config["EnableTranslation"] and not config["TranslateInterumResults"] and not final:
            continue

        text = None
        
        time_now = datetime.datetime.now()
        difference = time_now - last_disp_time
        if difference.total_seconds() < 1 and not final:
            continue
        
        if config["TranscriptionMethod"] in methods:
            method = methods[config["TranscriptionMethod"]]
        else:
            method = r.recognize_google

        try:
            #client.send_message("/chatbox/typing", True)
            text = method(ad, language=config["CapturedLanguage"])
            
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

        if text is None or text == "":
            continue

        current_text = text

        if last_text == current_text:
            continue

        last_text = current_text

        diff_in_milliseconds = difference.total_seconds() * 1000
        if diff_in_milliseconds < config["TranscriptionRateLimit"]:
            ms_to_sleep = config["TranscriptionRateLimit"] - diff_in_milliseconds
            print("[ProcessThread] Sending too many messages! Delaying by", (ms_to_sleep / 1000.0), "sec to not hit rate limit!")
            time.sleep(ms_to_sleep / 1000.0)

        
        if config["EnableTranslation"] and translator is not None: 
            try:
                trans = translator.translate(source_lang=config["CapturedLanguage"], target_lang=config["TranslateTo"], text=current_text)
                origin = current_text
                current_text = trans + " [%s->%s]" % (config["CapturedLanguage"], config["TranslateTo"])
                
                print("[ProcessThread] Recognized:",origin, "->", current_text)
            except Exception as e:
                print("[ProcessThread] Translating ran into an error!", e)
        else:
            print("[ProcessThread] Recognized:",current_text)

        if len(current_text) > 144:
            current_text = textwrap.wrap(current_text, width=144)[-1]

        last_disp_time = datetime.datetime.now()

        client.send_message("/chatbox/input", [current_text, True])

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
        buf_size = 0
        while True:
            audio = None
            try:
                audio = r.listen(source, phrase_time_limit=1, timeout=0.1)
            except WaitTimeoutError:
                if audio_buf is not None:
                    audio_queue.put((audio_buf, True))
                    audio_buf = None
                    buf_size = 0
                continue

            if audio is not None:
                if audio_buf is None:
                    audio_buf = audio
                else:
                    buf_size += 1
                    if buf_size > 10:
                        audio_buf = audio
                        buf_size = 0
                    else:
                        audio_buf = AudioData(audio_buf.frame_data + audio.frame_data, audio.sample_rate, audio.sample_width)
                    
                audio_queue.put((audio_buf, False))
                   

'''
OSC BLOCK
TODO: This maybe should be bundled into a class
'''
class OSCServer():
    def __init__(self):
        global config

        self.osc_port = get_open_udp_port()
        self.http_port = get_open_tcp_port()
        self.oscquery = OSCQueryService("VRCSubs-%i" % self.osc_port, self.http_port, self.osc_port)
        print("[OSCQuery] Running on HTTP port", self.http_port, "and UDP port", self.osc_port)

        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self._def_osc_dispatch)
        self.dispatcher.map("/avatar/parameters/MuteSelf", self._osc_muteself)

        # Set up the OSCQuery params -- VRChat will only automatically send if we advertise that we receive
        self.oscquery.advertise_endpoint("/avatar/parameters/MuteSelf",  get_state('selfMuted'), OSCAccess.WRITEONLY_VALUE)

        
        
        for key in config.keys():
            self.dispatcher.map(f"/avatar/parameters/vrcsub-{key}", self._osc_updateconf)
            self.oscquery.advertise_endpoint(f"/avatar/parameters/vrcsub-{key}", config[key], OSCAccess.WRITEONLY_VALUE)

        browser = OSCQueryBrowser()
        time.sleep(2)
        service = browser.find_service_by_name("VRChat-Client")
        
        if service is not None:
            oscq = OSCQueryClient(service)
            mute_self_node = oscq.query_node("/avatar/parameters/MuteSelf")
            
            # For safety, let's check if selfMuted actually exists (like below) before calling this
            # Some people on discord have this return None sometimes, maybe before VRC inits OSCQ?
            # May warrant further investigation...
            if mute_self_node is not None:
                set_state('selfMuted', mute_self_node.value[0])

            for key in config.keys():
                n = oscq.query_node(f"/avatar/parameters/vrcsub-{key}")
                if n is not None:
                    print(f"[OSCQuery] Config {key} -> {n.value[0]}")
                    config[key] = n.value[0]
            
            print("[OSCQuery] Loaded values from VRChat!")

        self.server = BlockingOSCUDPServer(("127.0.0.1", self.osc_port), self.dispatcher)
        self.server_thread = threading.Thread(target=self._process_osc)

        

    def launch(self):
        self.server_thread.start()

    def shutdown(self):
        self.server.shutdown()
        self.server_thread.join()

    def _osc_muteself(self, address, *args):
        print("[OSCThread] Mute is now", args[0])
        set_state("selfMuted", args[0])

    def _osc_updateconf(self, address, *args):
        key = address.split("vrcsub-")[1]
        print("[OSCThread]", key, "is now", args[0])
        config[key] = args[0]

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
        new_config = None
        with open(cfgfile, 'r') as f:
            new_config = load(f, Loader=Loader)
        if new_config is not None:
            for key in new_config:
                config[key] = new_config[key]

    # Start threads
    pst = threading.Thread(target=process_sound)
    pst.start()

    cat = threading.Thread(target=collect_audio)
    cat.start()
    
    osc = None
    launchOSC = False
    if config['FollowMicMute']:
        print("[VRCSubs] FollowMicMute is enabled in the config, speech recognition will pause when your mic is muted in-game!")
        launchOSC = True
    else:
        print("[VRCSubs] FollowMicMute is NOT enabled in the config, speech recognition will work even while muted in-game!")

    if config['AllowOSCControl']:
        print("[VRCSubs] AllowOSCControl is enabled in the config, will listen for OSC controls!")
        launchOSC = True

    if launchOSC:
        osc = OSCServer()
        osc.launch()

    pst.join()
    cat.join()
    
    if osc is not None:
        osc.shutdown()

if __name__ == "__main__":   
    main()