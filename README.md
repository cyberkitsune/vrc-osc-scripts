# vrc-osc-scripts
This repo contains various python OSC helper scripts that I made for VRChat, mostly stuff that interacts with the new chatbox api!

All these scripts require python3 and use pip for dependency management unless otherwise specified.

**Be sure to enable OSC in your VRChat radial menu before using these scripts!**

## VRCNowplaying
This script broadcasts what you're currently listening to your chatbox, grabbing the data from the Windows MediaManager API.

### Usage
First, install deps:
```
pip install -r VRCSubs/Requirements.txt
```

Then, just run the Script
```
python VRCNowPlaying/vrcnowplaying.py
```

Now, listen to some music and watch your chatbox!

### To-do
- [ ] Support customizing output format via yml
- [ ] Gif of this working
- [ ] Anything else?

## VRCSubs
This script attempts to auto-transcribe your microphone audio into chat bubbles using the Google Web Search Speech API (via the `SpeechRecognition` package) -- It's considered a prototype and has many issues, but is kinda neat!

### Usage
First, install deps:
```
pip install -r VRCSubs/Requirements.txt
```

Then, get in VR and launch the game, and **ensure your headset mic / mic you use is your default in windows!** (Setting a specific mic isn't supported yet)

Last, run the script
```
python VRCSubs/vrcsubs.py
```

The script should start listening to you right away and will send chatbox messages as you speak!

### Config
Some options can be configured in `VRCSubs/Config.yml` -- Just edit that file and check the comments to see what the options are!

### To-do
- [ ] Make the hacky audio-chunking I use cut off words less
- [ ] Consider alternative Speech-to-text API (The google one WILL rate limit me eventually...)
- [x] Communicate VRC mic mute status
- [ ] Support non-default mic
- [ ] Support VRC's chatbox rate-limit
- [ ] Voice commands to potentially pause / resume chatbox display?
- [ ] Add gif of this in action to this README
