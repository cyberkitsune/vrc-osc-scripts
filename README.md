# vrc-osc-scripts
This repo contains various python OSC helper scripts that I made for VRChat, mostly stuff that interacts with the new chatbox api!

All these scripts require python3 and use pip for dependency management unless otherwise specified.

**Be sure to enable OSC in your VRChat radial menu before using these scripts!**

If you don't have python installed already, and you are running Windows, get it [from here](https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe) **and be sure to click "Add Python to environment variables"** in the installer (Under Customize Install -> Advanced Options)

If you want a quick video tutorial on how to use these scripts, check this [video I made](https://www.youtube.com/watch?v=y9XOGtOaIV8)!

## VRCSubs
This script attempts to auto-transcribe your microphone audio into chat bubbles using the Google Web Search Speech API (via the `SpeechRecognition` package) -- It's considered a prototype and has many issues, but is kinda neat!

![VRCSubs in action!](https://raw.githubusercontent.com/cyberkitsune/vrc-osc-scripts/main/img/subtitles.gif)

### Usage
#### Auto
If you're on windows, try double-clicking `RunVRCSubs.bat` after installing python!

#### Manual
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

### OSC Avatar Control
You don't _need_ any avatar-specific setup to use VRCSubs! But if you'd like you can add some additional paramaters to make controlling it easier. For more information check out: [VRCSubs OSC Avatar Toggle Setup](https://github.com/cyberkitsune/vrc-osc-scripts/wiki/VRCSubs-OSC-Avatar-Toggle-Setup)

### Configuration
Some options can be configured in `VRCSubs/Config.yml` -- Just edit that file and check the comments to see what the options are!

#### Translation
There is a prototype live translation function in VRCSubs. It's considered a prototype and the output may not be very useful, but if you with to try it adjust the options `EnableTranslation` and `TranslateTo` in `VRCSubs/Config.yml`!

### To-do
- [x] ~~Make the hacky audio-chunking I use cut off words less~~
- [ ] Consider alternative Speech-to-text API
- [ ] Support swaping listened to / translated language via OSC input
- [ ] Make a self-updating standalone exe
- [ ] Support OSCQuery when it's out
- [x] ~~Communicate VRC mic mute status~~
- [ ] Support non-default mic / better handle mic switching
- [X] ~~Support VRC's chatbox rate-limit~~
- [x] ~~Add gif of this in action to this README~~


## VRCNowplaying
This script broadcasts what you're currently listening to your chatbox, grabbing the data from the Windows MediaManager API.

![VRCNowplaying in action!](https://raw.githubusercontent.com/cyberkitsune/vrc-osc-scripts/main/img/nowplaying.gif)

### Usage
#### Auto
If you're on windows, try double-clicking `RunVRCNowPlaying.bat` after installing python!

#### Manual
First, install deps:
```
pip install -r VRCNowPlaying/Requirements.txt
```

Then, just run the Script
```
python VRCNowPlaying/vrcnowplaying.py
```

Now, listen to some music and watch your chatbox!

### Config
Some options can be configured in `VRCNowPlaying/Config.yml` -- Just edit that file and check the comments to see what the options are!

### To-do
- [x] ~~Support customizing output format via yml~~
- [x] ~~Gif of this working~~
- [ ] Anything else?

