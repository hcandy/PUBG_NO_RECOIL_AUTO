import os
import threading
import time
import cv2 as cv
import pyttsx3 as pytts
import pyttsx3.drivers
import pyttsx3.drivers.sapi5
import json
import numpy as np

from mss import mss
import mss.tools as mss_tools
from pynput.keyboard import Listener

current_gun = ""  # 当前的武器名

current_gun_pos_id = 1  # 当前武器位

gun_list = []


# 枪名取对应的lua配置名
def get_gun_config_name(gun_name):
    # 枪械名字对应的配置 lua存在的不在这里写 没有枪械配置的先套用其他枪的配置
    with open('resource//dict//gun_dict.json', 'r') as f:
        gun_dict = json.load(f)

    return gun_dict.get(gun_name) or gun_name


# 保存配置到D盘根目录
def save_config(gun_name):
    file = "D:\\config.lua"
    with open(file, "w+") as file:
        file.write("fireMode='"+gun_name+"'")


# 对比图片特征点
def image_similarity_opencv(img1, img2):
    image1 = cv.imread(img1, 0)
    image2 = cv.cvtColor(img2, cv.COLOR_RGB2GRAY)

    orb = cv.ORB_create()
    kp1, des1 = orb.detectAndCompute(image1, None)
    kp2, des2 = orb.detectAndCompute(image2, None)
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    if des1 is None or des2 is None:
        return 0
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = []
    for m in matches:
        if m.distance <= 50:
            good_matches.append(m)
        pass
    return len(good_matches)


def similarity(im):
    global current_gun
    global gun_list

    for gun_name in gun_list:
        result = image_similarity_opencv(
            r"resource\\" + gun_name + ".png", im)
        if result >= 30:
            if current_gun != gun_name:
                current_gun = gun_name  # 避免重复操作
                print(gun_name+" deployed. slot " + str(current_gun_pos_id))
                save_config(get_gun_config_name(gun_name))
                play_sound(gun_name+" deployed. slot " + str(current_gun_pos_id))
            break


# 截屏
def screen():

    while True:
        similarity(screenshot())
        time.sleep(1)


# 播放声音
def play_sound(content):
    engine = pytts.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 200)  # 语速
    engine.setProperty('volume', 0.8)  # 音量
    engine.say(content)
    engine.runAndWait()
    engine.stop()
    pass


# 监听键盘输入
def on_release(key):
    global current_gun_pos_id
    try:
        key = int(key.char)
        if key == 1 or key == 2:
            current_gun_pos_id = key
    finally:
        return True


# 监听键盘输入
def keyboard_listener():
    listener = Listener(on_release=on_release)
    listener.start()
    listener.join()


def scan(img_dir):
    for files in os.listdir(img_dir):
        if os.path.splitext(files)[1] == '.png':
            gun_list.append(os.path.splitext(files)[0])


def screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        left = 1940
        top = 1325
        width = 195
        height = 100
        if current_gun_pos_id == 2:
            top = top - 80
            pass
        bbox = (left, top, left + width, top + height)

        shot = sct.grab(bbox)
        return np.array(bytearray(shot.rgb), dtype=np.uint8).reshape((height, width, 3))


# 程序入口
def main():
    os.system("title Solder76 Smart")
    os.system("mode con cols=32 lines=5")
    print("Solder 76 Smart lite")
    print("version 1.0 beta")

    scan("resource")

    play_sound("Tactical visor activated. ")
    threads = [threading.Thread(target=screen),
               threading.Thread(target=keyboard_listener)]
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()
