#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import json
import time
import random

UTCDIFF = 8

def ttime(gt_mode: str = 'all'):
    if gt_mode == 'all': return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + UTCDIFF*3600))
    temp_strs = {
        'all': '%Y-%m-%d %H:%M:%S',
        'year': '%Y',
        'mounth': '%m',
        'day': '%d',
        'hour': '%H',
        'minute': '%M',
        'second': '%S',
    }
    return int(time.strftime(temp_strs[gt_mode], time.localtime(time.time() + UTCDIFF*3600)))

def hlog(msg, msg_type = 'info'):
    if msg_type in ['info']: return
    print(f"{ttime()} - {msg_type}: {msg}")

def check_file(f_type: str, f_name: str, content: str = "{}"):
    if f_type == 'dir' and not os.path.isdir(f_name):
        if os.path.isfile(f_name): raise Exception(f"已存在同名文件 [{f_name}]，请检查系统所需文件夹路径是否被占用")
        else: os.mkdir(f_name)
    elif f_type == 'file' and not os.path.isfile(f_name):
        if os.path.isdir(f_name): raise Exception(f"已存在同名文件夹 [{f_name}]，请检查系统所需文件路径是否被占用")
        else:
            with open(f_name, 'w', encoding = 'utf8') as f: f.write(content)

HARDMODULEDIR = "HModules"
check_file('dir', HARDMODULEDIR)

CONFS = HARDMODULEDIR + "/conf"
check_file('dir', HARDMODULEDIR)

PORTID = 1

################################## 初始化各个模块 ##################################
from HModules import HActuator, HMySQL, HSensors, HConfig, HLog

sql = HMySQL.HSQL('HGreenhouse')
s_dht = HSensors.DHT(4)
spett = HSensors.IOSENSOR(26)
arelay = dict(zip(['fan', 'heat', 'air', 'uv'], [HActuator.HRELAY(pin) for pin in [5, 6, 13, 19]]))
afood = HActuator.SteeringEngine(20)
awater = HActuator.SteeringEngine(21)
log = HLog.LOG()

################################  定义各个功能模块  ################################

def module_1_food(conf) -> int:
    conf.updata('left_food', conf.data.get('left_food', 0))
    conf.updata('left_water', conf.data.get('left_water', 0))
    addFood = conf.get_data(['left_food']) < conf.get_data(['food'])
    addWater = conf.get_data(['left_water']) < conf.get_data(['water'])
    afood.switch(addFood)
    awater.switch(addWater)
    if addFood: conf.updata('left_food', conf.get_data(['left_food']) + 5)
    if addWater: conf.updata('left_water', conf.get_data(['left_water']) + 5)
    log.linfo(f"食物余量 [{conf.get_data(['left_food'])}] | 饮水余量 [{conf.get_data(['left_water'])}] | 正在加食 [{addFood}] | 正在加水 [{addWater}]")
    return 5 if addFood or addWater else 600

def module_2_actor(conf) -> int:
    msg = ""
    for k, act in arelay.items():
        act.run(conf.data[k])
        msg += f" {k}: {conf.data[k]} |"
    log.linfo("执行器状态" + msg)
    return 600

def module_3_pett(conf) -> int:
    havePet = spett.check()
    if havePet:
        pett = random.choice(range(16, 25))
        # if pett > 21:
        #     pett = f"{pett}\n在睡觉"
        # else:
        #     pett = f"{pett}\n没睡觉"
    else: pett = random.choice(range(0, 15))
    log.linfo(f"当前宠物温度是: {pett}")
    # else: pett = '宠物不在窝中'
    conf.updata("petTemperature", pett)
    return 60

def main():
    homeConf = {
        "food": 200,
        "water": 300,
        "fan": True,
        "heat": False,
        "air": True,
        "uv": False,
        "temperature": 25,
        "humidity": 70,
        "petTemperature": 18,
    }
    modules_run_info = {
        '1_food': {
            'last_run_time': time.time(),
            'run_interval': 6,
            'conf': HConfig.CONFIG(CONFS + '/home_conf', CONFS + '/home_conf_reset', homeConf)
        },
        '2_actor': {
            'last_run_time': time.time(),
            'run_interval': 6,
            'conf': HConfig.CONFIG(CONFS + '/home_conf', CONFS + '/home_conf_reset', homeConf)
        },
        '3_pett': {
            'last_run_time': time.time(),
            'run_interval': 6,
            'conf': HConfig.CONFIG(CONFS + '/home_conf', CONFS + '/home_conf_reset', homeConf)
        },
    }
    while True:
        for module in modules_run_info.keys():
            time.sleep(1)
            if modules_run_info[module]['conf'].reset():
                modules_run_info[module]['run_interval'] = 1
            if int(time.time() - modules_run_info[module]['last_run_time']) > modules_run_info[module]['run_interval']:
                modules_run_info[module]['run_interval'] = eval(f"module_{module}")(modules_run_info[module]['conf'])
                modules_run_info[module]['last_run_time'] = time.time()
            # try:
            #     if module['conf'].reset() or int(time.time() - modules_run_info[module]['last_run_time']) > modules_run_info[module]['run_interval']:
            #         modules_run_info[module]['run_interval'] = eval(f"module_{module}")(module['conf'])
            #         modules_run_info[module]['last_run_time'] = time.time()
            # except TypeError:
            #     hlog(f"main module = {module}", 'error')
            #     modules_run_info[module]['run_interval'] = 1

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        hlog('智能宠物屋硬件系统停止工作')

