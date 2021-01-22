import os
import threading
import time
import cv2 as cv
import pyttsx3 as pytts
import pyttsx3.drivers
import pyttsx3.drivers.sapi5
from PIL import ImageGrab

from pynput.keyboard import Listener

current_gun = ""  # 当前的武器名

current_gun_pos_id = 1  # 当前武器位

# 枪名取对应的lua配置名


def get_gun_config_name(gun_name):
    # 枪械名字对应的配置 lua存在的不在这里写 没有枪械配置的先套用其他枪的配置
    dict = {'GROZA': 'M416', 'MP5K': 'Vector',
            'Mini14': 'M16A4', 'Mk14': 'M16A4', 'SLR': 'M16A4'}
    return dict.get(gun_name) or gun_name

# 保存配置到D盘根目录


def save_config(gun_name):
    file = "D:\\config.lua"
    with open(file, "w+") as file:
        file.write("config='"+gun_name+"'")


# 对比图片特征点


def image_similarity_opencv(img1, img2):
    image1 = cv.imread(img1, 0)
    image2 = cv.imread(img2, 0)
    orb = cv.ORB_create()
    kp1, des1 = orb.detectAndCompute(image1, None)
    kp2, des2 = orb.detectAndCompute(image2, None)
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    if des1 is None or des2 is None:
        return 0
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    goodMatches = []
    for m in matches:
        if m.distance <= 50:
            goodMatches.append(m)
        pass
    return len(goodMatches)


def similarity():
    global current_gun
    gun_list = ['AKM', 'Beryl M762', 'G36C', 'GROZA', 'M16A4', 'M416', 'Mini14',
                'Mk14', 'MP5K', 'SCAR-L', 'SLR', 'SCAR-L', 'UMP45', 'Vector', 'QBZ']
    for gun_name in gun_list:
        result = image_similarity_opencv(
            r"resource\\" + gun_name + ".png", r'tmp\\tmp.png')
        if result >= 30:
            if current_gun != gun_name:
                current_gun = gun_name  # 避免重复操作
                print("切换武器," + gun_name+",当前武器," + str(current_gun_pos_id))
                save_config(get_gun_config_name(gun_name))
                play_sound("切换武器," + gun_name+",当前武器," +
                           str(current_gun_pos_id))
            break

# 截图


def screen():
    absPath = os.path.abspath('.')
    path = [x for x in os.listdir('.') if os.path.isdir(x)]
    if 'tmp' in path:
        pass
    else:
        pngPath = os.path.join(absPath, 'tmp')
        os.mkdir(pngPath)
        pass

    # 截屏

    def screenshot():
        x = 1940
        y = 1325
        # 切换二号武器 截图Y坐标向上移动80像素
        if current_gun_pos_id == 2:
            y = y - 80
            pass

        box = (x, y, x+195, y+100)
        im = ImageGrab.grab(box)
        im.save(r'tmp\\tmp.png')
        pass

    while True:
        screenshot()
        similarity()
        time.sleep(1)

# 播放声音


def play_sound(content):
    engine = pytts.init()
    engine.setProperty('rate', 220)  # 语速
    engine.setProperty('volume', 0.35)  # 音量
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

# 程序入口


def main():
    os.system("title Main")
    os.system("mode con cols=30 lines=30")
    print("         本软件免费使用!\n https://github.com/hcandy/PUBG_NO_RECOIL_AUTO\n 作者QQ:434461000")

    threads = [threading.Thread(target=screen),
               threading.Thread(target=keyboard_listener)]
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()
