"""
VRCSubs - A script to create "subtitles" for yourself using the VRChat textbox!
(c) 2022 CyberKitsune & other contributors.
"""
import speech_recognition as sr
from speech_recognition import UnknownValueError, WaitTimeoutError
import queue, threading, datetime
from pythonosc import udp_client

r = sr.Recognizer()
audio_queue = queue.Queue()

def process_sound():
    global audio_queue, r
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    current_text = ""
    last_disp_time = datetime.datetime.now()
    print("Starting audio processing!")
    while True:
        ai = audio_queue.get()
        text = None
        try:
            client.send_message("/chatbox/typing", True)
            text = r.recognize_google(ai)
        except UnknownValueError:
            client.send_message("/chatbox/typing", False)
            continue
        except TimeoutError:
            client.send_message("/chatbox/typing", False)
            client.send_message("/chatbox/input", ["[Timeout Error]", True])
            print("Timeout Error when recognizing speech!")
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

def main():
    global audio_queue, r
    mic = sr.Microphone()
    pst = threading.Thread(target=process_sound)
    pst.start()

    print("Starting audio collection!")
    with mic as source:
        while True:
            audio = None
            try:
                audio = r.listen(source, phrase_time_limit=3, timeout=1)
            except WaitTimeoutError:
                continue

            if audio is not None:
                audio_queue.put(audio)


if __name__ == "__main__":
    main()