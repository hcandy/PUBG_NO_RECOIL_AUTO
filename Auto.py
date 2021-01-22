import os
import threading
import time
import cv2 as cv
import pyttsx3 as pytts
import pyttsx3.drivers
import pyttsx3.drivers.sapi5
import win32api as winapi
from PIL import ImageGrab

from pynput.keyboard import Key, Controller, Listener

dict = {'Beryl M762': '0|0|0', 'AKM': '0|0|1', 'M416': '0|1|0', 'QBZ': '0|1|0', 'SCAR-L': '0|1|1', 'M16A4': '1|0|0',
        'Tommy Gun': "1|0|1", 'Vector': '1|1|0', 'UMP45': '1|1|1', 'G36C': '0|1|0', 'GROZA': '0|1|0', 'Mini14': '1|0|0',
        'Mk14': '1|0|0', 'SLR': '1|0|0', 'MP5K': '1|1|1', }


current_gun = ""  # 当前的武器名

current_gun_pos_id = 1  # 当前武器位

# logitech_handle = []  # 当前的罗技进程

# print(cv.__version__)


# def Start_Logitech_Driver():
#     global logitech_handle
#     logitech_handle = win32process.CreateProcess('C:\\Program Files\\Logitech Gaming Software\\LCore.exe', '/minimized',
#                                                  None, None, 0, win32process.CREATE_NO_WINDOW, None, None,
#                                                  win32process.STARTUPINFO())
#     pass


# def Kill_Logitech_Driver():
#     if logitech_handle:
#         win32process.TerminateProcess(logitech_handle[0], 0)
#     else:
#         os.system('taskkill /IM LCore.exe /F')
#     pass


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
    gun_list = ['AKM', 'Beryl M762', 'G36C', 'GROZA', 'M16A4',
                'M416', 'Mini14', 'Mk14', 'MP5K', 'SCAR-L', 'SLR', 'SCAR-L', 'UMP45', 'Vector', 'QBZ']
    for gun_name in gun_list:
        result = image_similarity_opencv(
            r"resource\\" + gun_name + ".png", r'tmp\\tmp.png')
        if result >= 30:
            if current_gun != gun_name:
                current_gun = gun_name  # 避免重复操作
                print("切换武器," + gun_name)

                print(dict[gun_name])
                change_key_state(dict[gun_name])

                play_sound("切换武器," + gun_name)
            break


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

# 更改按键状态
def change_key_state(content):
    strlist = content.split('|')
    numState = int(strlist[0])
    capState = int(strlist[1])
    scrState = int(strlist[2])
    keyboard = Controller()
    if winapi.GetKeyState(144) == numState:
        pass
    else:
        keyboard.press(Key.num_lock)
        keyboard.release(Key.num_lock)
    pass

    if winapi.GetKeyState(145) == scrState:
        pass
    else:
        keyboard.press(Key.scroll_lock)
        keyboard.release(Key.scroll_lock)
    pass

    if winapi.GetKeyState(20) == capState:
        pass
    else:
        keyboard.press(Key.caps_lock)
        keyboard.release(Key.caps_lock)
    pass


def play_sound(content):
    engine = pytts.init()
    engine.setProperty('rate', 220)
    engine.setProperty('volume', 0.5)
    engine.say(content)
    engine.runAndWait()
    engine.stop()
    pass


def on_release(key):
    global current_gun_pos_id
    try:
        key = int(key.char)
        if key == 1 or key == 2:
            current_gun_pos_id = key
    finally:
        return True

def keyboard_listener():
    listener = Listener(on_release=on_release)
    listener.start()
    listener.join()



if __name__ == '__main__':
    os.system("title Main")
    os.system("mode con cols=30 lines=30")
    print("         本软件免费使用!\n https://github.com/hcandy/PUBG_NO_RECOIL_AUTO\n 作者QQ:434461000")

    threads = [threading.Thread(target=screen),
               threading.Thread(target=keyboard_listener)]
    for t in threads:
        t.start()
    
