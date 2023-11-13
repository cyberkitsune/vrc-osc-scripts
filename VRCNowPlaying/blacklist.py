import threading, os, glob, time, re

BLACKLISTED_WORLDS = {"wrld_b2d9f284-3a77-4a8a-a58e-f8427f87ba79": "Club Orion"}

class NowPlayingWorldBlacklist():
    def __init__(self):
        self._last_world = ""
        self._last_logfile = ""
        self._log_monitor_thread = threading.Thread(target=self._do_log_monitor)
        self._running = True
        self._file = None

        self._log_monitor_thread.start()
        pass

    def _get_latest_logfile(self):
        lfglob = glob.glob(f"{os.getenv('USERPROFILE')}\\AppData\\LocalLow\\VRChat\\VRChat\\output_log_*.txt")

        # Grab latest I think?
        lfglob.sort(reverse=True)

        return lfglob[0]

    def _do_log_monitor(self):
        print("[WorldBlacklist] Starting world monitor!")
        while self._running:
            # First, check if we're a new logfile. If we are, let's parse it and catch up.
            if self._last_logfile != self._get_latest_logfile():
                print(f"[Blacklist] New logfile! {self._get_latest_logfile()}")
                if self._file is not None:
                    self._file.close()
                self._last_logfile = self._get_latest_logfile()
                self._file = open(self._last_logfile, 'r', encoding="utf-8")

                # Pass through all lines
                for line in self._file.readlines():
                    self._parse_logfile_line(line)

                # All caught up, seek to end
                self._file.seek(0, 2)

                # Sleep a lil
                time.sleep(0.1)
                continue
        
            if self._file is not None:
                line = self._file.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                self._parse_logfile_line(line)


    def _parse_logfile_line(self, line):
        r = re.findall(r'Fetching world information for (wrld_.*)', line)
        if len(r) > 0:
           if self._last_world != r[0]:
                print(f"[Blacklist] New world: {r[0]}")
                self._last_world = r[0]

    def is_current_blacklisted(self):
        if self._last_world in BLACKLISTED_WORLDS:
            return (True, BLACKLISTED_WORLDS[self._last_world])
        
        return (False, '')