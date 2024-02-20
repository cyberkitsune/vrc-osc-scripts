import threading, os, glob, time, re, requests

BLACKLIST_REPO = "https://github.com/cyberkitsune/chatbox-club-blacklist/raw/master/npblacklist.json"

class NowPlayingWorldBlacklist():
    def __init__(self):
        self._last_world = ""
        self._last_logfile = ""
        self._log_monitor_thread = threading.Thread(target=self._do_log_monitor)
        self._running = True
        self._file = None
        self._blacklisted_worlds = {}

        self._log_monitor_thread.start()
        self._fetch_current_blacklist()
        pass

    def _fetch_current_blacklist(self):
        print("[WorldBlacklist] Fetching world blacklist...")
        r = requests.get(BLACKLIST_REPO)
        if r.status_code != 200:
            raise Exception("Unable to fetch current blacklist!")
        
        js = r.json()
        for world in js['worlds']:
            self._blacklisted_worlds[world['id']] = world['name']

        print(f"[WorldBlacklist] Loaded {len(self._blacklisted_worlds)} worldids.")

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
                self._last_world = r[0]

    def is_current_blacklisted(self):
        if self._last_world in self._blacklisted_worlds:
            return (True, self._blacklisted_worlds[self._last_world])
        
        return (False, '')