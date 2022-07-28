# requires libmpv (via system package manager), python-mpv (via pip) and apscheduler (via pip)
import mpv
import os
import time
from datetime import datetime
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler


n = 0

path = "/home/hendrik/Desktop/IR-Cam-Captures/" + input("Enter the folder name where your captures shall be saved. It must not contain any spaces, use - instead!\n(They'll be saved under /home/hendrik/Desktop/IR-Cam-Captures/<your-folder-name>. You can also speccify a subfolder by entering something like <my-name/my-subfolder>): ")
if os.path.exists(path) != True: os.makedirs(path)

interval = int(input("At what time interval [s] should the captures be made?: "))

repeats = int(input("How many captures do you want to save?: "))

print(f"\nThe experiment will take {interval * (repeats - 1)} seconds.\n")
print("Press 's' to start the experiment, when you're done focusing.\n")
print("Starting preview in 5 seconds.")
time.sleep(5)


def save_image():
    print(f"Capturing screenshot {n+1} at {datetime.now()}")
    pillow_img = player.screenshot_raw()
    pillow_img.save(f"{path}/Screenshot {datetime.now()}.png", compress_level=0)


def listener(event):
    global n
    if event.code == 4096:
        print("Job executed")
        n = n + 1
    else:    
        print(event)


scheduler = BackgroundScheduler()
scheduler.add_job(save_image, 'interval', seconds=interval)
scheduler.add_listener(listener, apscheduler.events.EVENT_JOB_EXECUTED)


player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, terminal=True, input_terminal=True)
player["vo"] = "gpu"
#player["gpu-context"] = "drm"
player["demuxer-lavf-format"] = "video4linux2"
player["demuxer-lavf-o"] = "video_size=1920x1080,input_format=mjpeg"
player.profile = "low-latency"
player.untimed = True

@player.on_key_press("s")
def my_s_binding():
    print(f"Beginning experiment with {repeats} captures in an interval of {interval} seconds.")
    scheduler.start()
    while True:
        time.sleep(0.5)
        if n == repeats:
            scheduler.shutdown()
            break
        else:
            print("Experiment still running, waiting for completion ...")
    print("\n\nExperiment done!\n")
    os._exit(0)

player.play("av://v4l2:/dev/video0")
player.wait_for_playback()