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

