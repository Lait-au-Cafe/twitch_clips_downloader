import sys
import os
import time
import urllib.error
import urllib.request
import re
import datetime
import tzlocal
import json
from collections import OrderedDict
from twitchAPI.twitch import Twitch
import eel

# Load configurations
with open("./config.json") as config_file:
    configs = json.load(config_file, object_pairs_hook=OrderedDict)

# Define util functions
@eel.expose
def get_cache(): return configs['cache']

def download(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as dst_file:
                dst_file.write(data)
    except urllib.error.URLError as e: print(e)

@eel.expose
def download_clips(target_channel_id, target_year, target_month):
    # save cache
    configs['cache']['twitch_id'] = target_channel_id

    timezone = tzlocal.get_localzone()
    from_date = datetime.datetime(target_year, target_month, 1, tzinfo=timezone)
    if target_month == 12:
        until_date = datetime.datetime(target_year + 1, 1, 1, tzinfo=timezone)
    else:
        until_date = datetime.datetime(target_year, target_month + 1, 1, tzinfo=timezone)

    twitch = Twitch(configs['auth']['app_id'], configs['auth']['app_secret'])
    twitch.authenticate_app([])
    user = twitch.get_users(logins=target_channel_id)['data'][0]

    dl_dir = f"./clips/{target_channel_id}_{target_year}年{target_month}月分/"
    os.makedirs(dl_dir, exist_ok=True)

    cursor = None
    while True:
        clips = twitch.get_clips(broadcaster_id=user['id'], after=cursor, ended_at=until_date, started_at=from_date)
        for clip in clips['data']:
            creator_name = repr(clip['creator_name'])[1:-1]
            clip_url = re.sub(r'-preview.*', '.mp4', clip['thumbnail_url'])
            filename = repr(str.strip(re.sub(r'[<>:"\/\\\|\?\*]', "", clip['title'])))[1:-1]
            print(f"Downloading {filename} by {creator_name}")
            download(clip_url, dl_dir + f"「{filename}」-{creator_name}.mp4")

        cursor = clips['pagination'].get('cursor', None)
        if cursor is None: break
    
    print("Completed. ")

def save_configs(route, websockets):
    with open("./config.json", 'w') as config_file:
        json.dump(configs, config_file, indent=4, ensure_ascii=False)

    time.sleep(1.0)
    if len(websockets) == 0: sys.exit()

# Start eel
eel.init("web")
eel.start("index.html", close_callback=save_configs)