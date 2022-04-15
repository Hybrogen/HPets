# -*- coding: utf-8 -*-

import time

from RPi import GPIO

GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)

class IOSENSOR(object):
    def __init__(self, pin, trigger = False):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN) 
        self.trigger = trigger

    def set_pin(self, pin):
        GPIO.cleanup()
        self.pin = pin

    def check(self) -> bool:
        return GPIO.input(self.pin) == self.trigger

    def __del__(self):
        GPIO.cleanup()

import Adafruit_DHT

class DHT(IOSENSOR):
    def __init__(self, pin, dht_type = 'DHT11'):
        self.pin = pin
        self.dht = Adafruit_DHT.DHT11 if dht_type == 'DHT11' else Adafruit_DHT.DHT22

    def check(self):
        h, t = Adafruit_DHT.read(self.dht, self.pin)
        time.sleep(3)
        if h and t and t > -271 and t < 100:
            rdata = {'temperature': int(t), 'humidity': int(h), 'state': 'ok'}
        else:
            rdata = {'state': 'error'}
        return rdata

class Hx711():
    def __init__(self, sckpin, dtpin):
        self.SCK = sckpin    # 物理引脚第11号，时钟
        self.DT = dtpin     #物理引脚第13号，数据
        self.flag = 1      #用于首次读数校准
        self.initweight = 0	#毛皮
        self.weight = 0		#测重
        self.delay = 0.09		#延迟时间
        GPIO.setup(self.SCK, GPIO.OUT)      # Set pin's mode is output
        GPIO.setup(self.DT, GPIO.IN)
        GPIO.setup(self.DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def check(self):
        GPIO.output(self.SCK,0)
        if GPIO.input(self.SCK): time.sleep(self.delay)
        value = 0
        while GPIO.input(self.DT): time.sleep(self.delay)
        #循环24次读取数据
        for i in range(24):
            GPIO.output(self.SCK, 1)
            if not GPIO.input(self.SCK): time.sleep(self.delay)
            value <<= 1		#左移一位，相当于乘2，二进制转十进制
            GPIO.output(self.SCK, 0)
            if GPIO.input(self.SCK): time.sleep(self.delay)
            if GPIO.input(self.DT): value += 1
        GPIO.output(self.SCK, 1)
        GPIO.output(self.SCK, 0)
        value = int(value/1905)		#1905为我传感器的特性值，不同传感器值不同。可先注释此步骤，再去测一物体A得到一个值X,而后用X除以A的真实值即可确定特性值
        #第一次读数为毛皮
        if self.flag: self.flag, self.initweight = 0, value
        #当前值减毛皮得测量到的重量
        else: self.weight = abs(value-self.initweight)
        if self.weight < 5: self.initweight = value
        return self.weight

if __name__ == '__main__':
    # s = IOSENSOR(7)
    s = DHT(23, 'DHT22')
    while True:
        try:
            print(f"{s.check()}    ", end = '\n')
            time.sleep(1)
        except Exception as e:
            print(f"Error {e}")
            del s
            break

