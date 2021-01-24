import os
import threading
import time
import win32con
import win32gui
import win32ui
import cv2 as cv
import pyttsx3 as pytts
import pyttsx3.drivers
import pyttsx3.drivers.sapi5
from PIL import ImageGrab
from queue import Queue
from pynput.keyboard import Listener, Key


q = Queue()

current_gun = {1: "", 2: ""}  # 当前的武器名

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
    goodMatches = 0
    for m in matches:
        if m.distance <= 50:
            goodMatches = goodMatches+1
        pass
    return goodMatches


def similarity(gun_pos):
    gun_list = ['AKM', 'Beryl M762', 'G36C', 'GROZA', 'M16A4', 'M416', 'Mini14',
                'Mk14', 'MP5K', 'SCAR-L', 'SLR', 'SCAR-L', 'UMP45', 'Vector', 'QBZ']
    for gun_name in gun_list:
        result = image_similarity_opencv(
            r"resource\\" + gun_name + ".png", r'tmp\\tmp.png')
        if result >= 25:
            if current_gun[gun_pos] != gun_name:
                current_gun[gun_pos] = gun_name  # 避免重复操作
                print("切换武器," + gun_name+",当前武器," +
                      str(gun_pos))
                save_config(get_gun_config_name(gun_name))
                play_sound("切换武器," + gun_name+",当前武器," +
                           str(gun_pos))
            else:  # 只在第一次拿到这把枪的时候才播报语音吧 感觉有点卡 第二次切换的时候直接保存配置
                save_config(get_gun_config_name(gun_name))
                print("切换武器," + gun_name+",当前武器," +
                      str(gun_pos))
            return True
    return False


# 截图
def screen(gun_pos):
    absPath = os.path.abspath('.')
    path = [x for x in os.listdir('.') if os.path.isdir(x)]
    if 'tmp' in path:
        pass
    else:
        pngPath = os.path.join(absPath, 'tmp')
        os.mkdir(pngPath)
        pass

    def screenshot():
        x = 1940
        y = 1325
        if gun_pos == 2:
            y = y - 80
            pass
        x_size = 195
        y_size = 100
        hwndDC = win32gui.GetWindowDC(0)  # 0表示当前活跃的窗口
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, x_size, y_size)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (x_size, y_size),
                      mfcDC, (x, y), win32con.SRCCOPY)
        saveBitMap.SaveBitmapFile(saveDC, "tmp\\tmp.png")

    n = 0
    while True:
        screenshot()
        if similarity(gun_pos):  # 如果返回True 退出循环
            break
        n = n+1
        if n >= 5:  # 如果5次还没有识别出来 退出循环
            break
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
    try:
        key = int(key.char)
        if key == 1 or key == 2:
            q.queue.clear()  # 每次按下 1 或者 2  清空掉之前的队列
            q.put(key)

    finally:
        return True

# 消费者


def consumer():
    while True:
        key = q.get()
        screen(key)
        q.task_done()

# 监听键盘输入


def keyboard_listener():
    listener = Listener(on_release=on_release)
    listener.start()

# 程序入口


def main():
    os.system("title Main")
    os.system("mode con cols=30 lines=30")
    print("         本软件免费使用!\n https://github.com/hcandy/PUBG_NO_RECOIL_AUTO\n 作者QQ:434461000")
    threads = [threading.Thread(target=consumer),
               threading.Thread(target=keyboard_listener)]
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()
