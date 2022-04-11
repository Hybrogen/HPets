#-*- coding:utf-8 -*-

import time
import os

import RPi.GPIO as GPIO

GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)

class HRELAY(object):
    def __init__(self, pin: int, trigger: bool = False):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.trigger = trigger
        self.run(not trigger)

    def set_pin(self, pin: int):
        GPIO.cleanup()
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def run(self, state: bool):
        GPIO.output(self.pin, state == self.trigger)

    def check(self) -> bool:
        return GPIO.input(self.pin) == self.trigger

    def __del__(self):
        GPIO.cleanup()

class SteeppingMOTOR(object):
    def __init__(self, pins: list):
        self.pins = pins
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)
        self.phases = [
                [1, 0, 0, 1], # 1
                [1, 0, 0, 0], # 2
                [1, 1, 0, 0], # 3
                [0, 1, 0, 0], # 4
                [0, 1, 1, 0], # 5
                [0, 0, 1, 0], # 6
                [0, 0, 1, 1], # 7
                [0, 0, 0, 1], # 8
                ]

    def run(self, mode: bool, run_duration: int = 3):
        stime = time.time()
        while int(time.time() - stime) < run_duration:
            for phase in (self.phases if mode else self.phases[::-1]):
                for pin, state in zip(self.pins, phase):
                    GPIO.output(pin, state)
                time.sleep(0.001)
        for pin in self.pins: GPIO.output(pin, False)

    def set_pin(self, pins: list):
        GPIO.cleanup()
        self.pins = pins
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

    def __del__(self):
        GPIO.cleanup()

from aip import AipFace
import picamera
import base64

class CAM(object):
    def __init__(self):
        APP_ID = '24809680'
        API_KEY = 'L12hPpoajGCWrMDjOlQUZZFP'
        SECRET_KEY = 'ZYlffa0VTG9yzEBDcRG9DgvQY0ej8BOv'
        self.baiduCloud = AipFace(APP_ID, API_KEY, SECRET_KEY)
        self.photoPath = "/tmp/HCamHCaptureHPhoto.jpg"
        self.baseFaces = "HModules/baseFaces"
        if not os.path.isdir(self.baseFaces): os.mkdir(self.baseFaces)

    def picture(self, outPath = None):
        if not outPath: outPath = self.photoPath
        with picamera.PiCamera() as camera:
            camera.start_preview()
            camera.capture(outPath)
            camera.stop_preview()

    def face(self):
        # if not os.path.isfile(self.photoPath): self.picture()
        self.picture()
        with open(self.photoPath,'rb') as f:
            base64_data = str(base64.b64encode(f.read()), 'utf-8')
        fi_option = {'max_face_num': 8, 'max_user_num': 10,}
        bcii = self.baiduCloud.multiSearch(base64_data, 'BASE64', 'models', fi_option)
        rdata = {'state': 'error'}
        try:
            faces = bcii['result']['face_list']
            if int(faces[0]['user_list'][0]['score']) > 90:
                rdata['state'] = 'ok'
                rdata['name'] = faces[0]['user_list'][0]['user_id']
                return rdata
        except TypeError:
            rdata['info'] = 'Match nothing'
            return rdata
        rdata['info'] = 'Match error'
        return rdata

    def get_user_info(self, userId):
        faces = self.baiduCloud.faceGetlist(userId, 'models')['result']['face_list']
        rdata = {
            'userId': userId,
            'recordTime': faces[0]['ctime'],
            'updataTime': faces[-1]['ctime'],
        }
        with open(f"{self.baseFaces}/{userId}.jpg", 'rb') as f:
            rdata['face'] = str(base64.b64encode(f.read()), 'utf-8')
        return rdata

    def get_faces(self):
        names = self.baiduCloud.getGroupUsers('models')['result']['user_id_list']
        faces = list()
        for name in names:
            face = self.baiduCloud.faceGetlist(name, 'models')['result']['face_list'][0]
            faces.append(face)
            time.sleep(1)
        return faces

    def add_user(self, userId):
        with open(f"{self.baseFaces}/{userId}.jpg", 'rb') as f:
            base64_data = str(base64.b64encode(f.read()), 'utf-8')
        self.baiduCloud.addUser(base64_data, 'BASE64', 'models', userId)

if __name__ == '__main__':
    '''
    a = HRELAY(4)
    print(a.check())
    a.set_output(True)
    print(a.check())
    a.set_output(False)
    print(a.check())
    s = SteeppingMOTOR([6, 13, 19, 26])
    s.run(True)
    s.run(False, 10)
    '''
    cam = CAM()
    # print(cam.face())
    print(f"faces = {cam.get_user_info('hon')}")

