#-*- coding:utf-8 -*-

import time

class LOG(object):
    def __init__(self, types: list = ['info', 'error', 'data']):
        self.types = dict(zip(types, [True]*len(types)))

    def log(self, msg: str, msgType: str):
        if not self.types.get(msgType, True): return
        loggingDate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(f"""{loggingDate} {'['+msgType+']':<10} - {msg}""")

    def linfo(self, msg):
        self.log(msg, 'info')

    def ldata(self, msg):
        self.log(msg, 'data')

    def lerror(self, msg):
        self.log(msg, 'error')

    def open_type(self, pointType: str = 'all'):
        if pointType != 'all':
            self.types[pointType] = True
        else:
            for k in self.types.keys():
                self.types[k] = True

    def close_type(self, pointType: str = 'all'):
        if pointType != 'all':
            self.types[pointType] = False
        else:
            for k in self.types.keys():
                self.types[k] = False

if __name__ == '__main__':
    log = LOG()
    log.linfo("输出日志")

