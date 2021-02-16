import os
import threading
import time
import json
import pynput
import cv2 as cv
import numpy as np
import pyttsx3 as pytts
# import pyttsx3.drivers
# import pyttsx3.drivers.sapi5
from mss import mss
from queue import Queue
from pynput.mouse import Button

q = Queue()

current_gun = {1: "", 2: ""}  # 当前的武器名

player_posture = 1  # 姿势 1为站 2为蹲 3为趴(暂时不用) 默认1

player_bullets = 1

gun_list = []

gun_dict = {}

job = None


class Job(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()     # 用于暂停线程的标识
        # self.__flag.set()       # 设置为True
        self.__running = threading.Event()      # 用于停止线程的标识
        self.__running.set()      # 将running设置为True

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()      # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
            posture()  # 姿势判断
            bullets()  # 子弹数量判断

    def pause(self):
        self.__flag.clear()     # 设置为False, 让线程阻塞

    def resume(self):
        self.__flag.set()    # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()       # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()        # 设置为False


class Action(object):
    # action_type 定义: True 为切换武器  False 为切换姿势
    def __init__(self, action_type, param):
        self.action_type = action_type
        self.param = param

    def get_type(self):
        return self.action_type

    def get_param(self):
        return self.param

# 播放声音



def play_sound(content):
    engine = pytts.Engine()
    engine.setProperty('rate', 220)  # 语速
    engine.setProperty('volume', 0.35)  # 音量
    engine.say(content)
    engine.runAndWait()
    engine.stop()

    


# 枪名取对应的lua配置名


def get_gun_config_name(gun_name):
    return gun_dict.get(gun_name) or gun_name


# 保存数据


def save_config(title, content):
    file = "D:\\"+title+".lua"
    with open(file, "w+") as file:
        file.write(title+"='"+content+"'")

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
    goodMatches = 0
    for m in matches:
        if m.distance <= 50:
            goodMatches = goodMatches+1
    return goodMatches


def similarity(im, gun_pos):
    for gun_name in gun_list:
        result = image_similarity_opencv(
            r"resource\\" + gun_name + ".png", im)
        if result >= 25:
            if current_gun[gun_pos] != gun_name:
                current_gun[gun_pos] = gun_name  # 避免重复操作
                play_sound("切换武器," + gun_name+",当前武器," + str(gun_pos))
            print("切换武器:" + gun_name+"  当前武器:" + str(gun_pos) +
                  "  当前姿势:" + ("站" if player_posture == 1 else "蹲"))
            save_config("config", get_gun_config_name(gun_name))
            return True
    return False

# 判断姿势


def posture():
    global player_posture
    left = 960
    top = 1305
    width = 5
    height = 5
    box = (left, top, left + width, top + height)
    img = screenshot(box)
    r, g, b = img.pixel(3, 3)
    if r < 180 and g < 180 and b < 180:
        posture = 2
    else:
        posture = 1
    
    save_config("posture", str(posture))

# 子弹数量判断


def bullets():
    global player_bullets
    left = 1273
    top = 1323
    width = 5
    height = 5
    box = (left, top, left + width, top + height)
    img = screenshot(box)
    r, g, b = img.pixel(3, 3)
    
    if r == 255:
        bullets = 0
    else:
        bullets = 1

    save_config("bullets", str(bullets))
    if bullets != player_bullets and bullets == 0:
        player_bullets = bullets
        play_sound("子弹耗尽")

# 截屏


def screen(gun_pos):
    left = 1940
    top = 1325
    width = 195
    height = 100
    if gun_pos == 2:
        top = top - 80
        pass
    box = (left, top, left + width, top + height)
    n = 0
    while True:
        img = screenshot(box)
        arr = np.array(img.pixels, dtype=np.uint8)
        if similarity(arr, gun_pos):  # 如果返回True 退出循环
            break
        n = n + 1
        if n >= 5:  # 如果5次还没有识别出来 退出循环1
            break
        time.sleep(1)


# 消费者


def consumer():
    while True:
        action = q.get()
        if action.get_type():
            screen(action.get_param())
        else:
            # 鼠标右键按下时 检测是蹲还是站
            posture(action.get_param())
        q.task_done()


# 监听键盘输入
def on_release(key):
    try:
        key = int(key.char)
        if key == 1 or key == 2:
            q.queue.clear()  # 每次按下 1 或者 2  清空掉之前的队列
            action = Action(True, key)
            q.put(action)
    finally:
        return True

# 监听键盘输入


def keyboard_listener():
    with pynput.keyboard.Listener(
            on_release=on_release) as listener:
        listener.join()


# 监听鼠标按键
def on_click(x, y, button, pressed):
    if Button.right == button:
        if pressed:
            # q.queue.clear()  # 每次按下 1 或者 2  清空掉之前的队列
            # action = Action(False, 0.5)
            # q.put(action)
            job.resume()  # 开始检测
        else:
            job.pause()  # 停止检测


# 监听鼠标按键
def mouse_listener():
    with pynput.mouse.Listener(
            on_click=on_click) as listener:
        listener.join()


# 初始化配置
def initialize(img_dir):
    for files in os.listdir(img_dir):
        if os.path.splitext(files)[1] == '.png':
            gun_list.append(os.path.splitext(files)[0])
    global gun_dict
    # 枪械名字对应的配置 lua存在的不在这里写 没有枪械配置的先套用其他枪的配置
    with open(r'resource//dict//gun_dict.json', 'r') as f:
        gun_dict = json.load(f)


def screenshot(box):
    with mss() as sct:
        shot = sct.grab(box)
        return shot


# 程序入口
def main():
    global job
    os.system("title Main")
    os.system("mode con cols=50 lines=30")
    print("                   本软件免费使用!\n https://github.com/hcandy/PUBG_NO_RECOIL_AUTO\n                   作者QQ:434461000")

    initialize("resource")

    job = Job()

    threads = [threading.Thread(target=consumer), threading.Thread(
        target=keyboard_listener), threading.Thread(target=mouse_listener), job]
    for t in threads:
        t.start()


if __name__ == '__main__':
    main()
