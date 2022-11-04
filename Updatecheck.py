import requests, os, json, zipfile, io, glob, shutil

API_BASE = "https://api.github.com"
REPO_OWNER = "cyberkitsune"
REPO_NAME = "vrc-osc-scripts"
REPO_BRANCH = "main"

def fetch_last_commit_info():
    # /repos/:owner/:repo/commits/master
    r = requests.get(f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits/{REPO_BRANCH}")
    js = r.json()
    return js['sha'], js['commit']['author']['name'], js['commit']['message']

def fetch_latest_repo_zip():
    print("[Updatecheck] Updating zip...")
    r = requests.get(f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/zipball/{REPO_BRANCH}")
    return r.content

def save_json(hash, author, message):
    with open("version.json", 'w') as f:
        f.write(json.dumps({'hash': hash, 'author': author, 'message': message}))

def load_json():
    js = None
    with open("version.json", "r") as f:
        js = json.load(f)
    return js

if __name__ == "__main__":
    if os.path.exists(".git"):
        print("[Updatecheck] You are using git! Please run \"git pull\" manually to update.")
        exit(0)

    hash, author, message = fetch_last_commit_info()
    if not os.path.exists("version.json"):
        save_json("0", author, message)
    
    last_info = load_json()
    if last_info['hash'] == hash:
        print("[Updatecheck] Scripts up to date!")
        exit(0)
    
    print(f"[Updatecheck] Updating to version {hash}!")
    print(f"[Updatecheck] Commit: {message} - {author}")

    update_zip = fetch_latest_repo_zip()
    with zipfile.ZipFile(io.BytesIO(update_zip), 'r') as zf:
        for file in zf.filelist:
            if file != "Config.yml":
                print(f"[Updatecheck] Extracting {file}")
                zf.extract(file, "update")
    
    update_folder = glob.glob(f"./update/{REPO_OWNER}-{REPO_NAME}-*", recursive=True)
    if len(update_folder) < 0:
        print("[Updatecheck] Can't find extracted zip?")
        exit(1)

    update_folder = update_folder[0]
    shutil.copytree(update_folder, os.getcwd(), dirs_exist_ok=True, ignore=shutil.ignore_patterns("*/Config.yml"))
    
    shutil.rmtree(update_folder, ignore_errors=True)

    save_json(hash, author, message)
    print("[Updatecheck] Update complete!")
            

    