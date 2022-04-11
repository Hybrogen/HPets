#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import json
import time

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

CONFS = HARDMODULEDIR + '/conf'
if not os.path.isdir(CONFS): os.mkdir(CONFS)

PORTID = 1

################################## 初始化各个模块 ##################################
from HModules import HActuator, HMySQL, HSensors, HConfig, HLog

# 数据库
sql = HMySQL.HSQL('HHOME')
# 传感器
s_dht = HSensors.DHT(25, 'DHT22')
# Adoor = HActuator.SteeppingMOTOR([6, 13, 19, 26])
Adoor = HActuator.SteeppingMOTOR([6, 13, 19, 26])
Aheater = HActuator.HRELAY(16)
Ahumidifier = HActuator.HRELAY(20)
Afan = HActuator.HRELAY(21)
lightIds = [1, 2]
lightPins = [19, 26]
Alight = dict(zip(lightIds, [HActuator.HRELAY(pin) for pin in lightPins]))
# 其他模块
log = HLog.LOG()
lightConf = HConfig.CONFIG(CONFS + '/light_conf', CONFS + '/light_conf')

################################  定义各个功能模块  ################################

def module_1_environment(conf) -> int:
    start_run_time = time.time()
    data = s_dht.check()
    if data.get('state') == 'error': return
    data['pid'] = PORTID
    sql.dht_save(data)
    humidity, temperature = data['humidity'], data['temperature']

    log.ldata(f"检测到温湿度数据: data = {data}")
    humiLow = humidity < conf.get_data(['humidity'])[0]
    humiHigh = humidity > conf.get_data(['humidity'])[1]
    tempLow = temperature < conf.get_data(['temperature'])[0]
    tempHigh = temperature > conf.get_data(['temperature'])[1]

    Ahumidifier.run(humiLow)
    conf.updata('water', [True, humiLow])
    Aheater.run(tempLow)
    conf.updata('heat', [True, tempLow])
    Afan.run(humiHigh or tempHigh)
    conf.updata('fan', [True, humiHigh or tempHigh])
    return (10 if sum([conf.get_data([f, 1]) for f in ['water', 'heat', 'fan']]) else 600) - int(time.time() - start_run_time)

# 大材小用这个厉害的接口，以后尽快改掉
import requests
def get_uv(city: str = 'Pingdingshan'):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=93835eae1c46dc657e84b40bf584dc0c"
    for i in range(3):
        try:
            rdata = json.loads(requests.request('GET', url = url).text)
        except requests.exceptions.ConnectionError:
            log.lerror(f"get_uv 请求失败，正在重试 {i + 1}")
            time.sleep(3)
    if rdata['cod'] != 200: return 0
    rdata = rdata['coord']
    url = f"https://openweathermap.org/data/2.5/onecall?lat={rdata['lat']}&lon={rdata['lon']}&units=metric&appid=439d4b804bc8187953eb36d2a8c26a02"
    for i in range(3):
        try:
            rdata = json.loads(requests.request('GET', url = url).text)
        except requests.exceptions.ConnectionError:
            log.lerror(f"get_uv 请求失败，正在重试 {i + 1}")
            time.sleep(3)
    rdata = rdata['current']['uvi']
    return rdata

def light_on(state: bool):
    for lid, l in Alight.items():
        if lid not in lightConf.get_data(): continue
        l.run(state)

def module_2_curtain(conf) -> int:
    start_run_time = time.time()
    data = {'pid': PORTID}
    log.linfo("请求光照数据...")
    data['light'] = get_uv('Hangzhou')
    log.ldata(f"请求到光照数据 uv = {data['light']} | cost {int(time.time() - start_run_time)}s")
    sql.light_save(data)

    lightOn = data['light'] < conf.get_data(['light'])
    light_on(lightOn)

    conf.updata('curtain_auto', True)
    conf.updata('curtain_state', lightOn)

    return 600 - int(time.time() - start_run_time)

def main():
    r"""
    主控程序
    执行逻辑：
    1. 无限循环
    2. 先重置配置文件
    3. 遍历所有模组
    4. 判断模组是否到达执行周期
    5. 执行模组函数
    """
    dhtConf = {
        'temperature': [20, 28],
        'humidity': [40, 80],
        'water': [True, False],
        'heat': [True, False],
        'fan': [True, False],
    }
    curtainConf = {
        'light': 5,
        'curtain_auto': True,
        'curtain_state': False,
    }
    # MRI - modules_run_info
    MRI = {
        'module_1_environment': {
            'last_run_time': time.time(),
            'run_interval': 6,
            'config': HConfig.CONFIG(CONFS + '/dht_conf', CONFS + '/dht_conf_reset', dhtConf),
        },
        'module_2_curtain': {
            'last_run_time': time.time(),
            'run_interval': 6,
            'config': HConfig.CONFIG(CONFS + '/curtain_conf', CONFS + '/curtain_conf_reset', curtainConf),
        },
    }
    while True:
        for module in MRI.keys():
            if MRI[module]['config'].reset(): MRI[module]['run_interval'] = 1
            time.sleep(1)
            if int(time.time() - MRI[module]['last_run_time']) > MRI[module]['run_interval']:
                MRI[module]['run_interval'] = eval(module)(MRI[module]['config'])
                MRI[module]['last_run_time'] = time.time()
            # try:
            #     if int(time.time() - MRI[module]['last_run_time']) > MRI[module]['run_interval']:
            #         MRI[module]['run_interval'] = eval(module)(MRI[module]['config'])
            #         MRI[module]['last_run_time'] = time.time()
            # except TypeError:
            #     log.lerror(f"main module = {module}")
            #     MRI[module]['run_interval'] = 1

if __name__ == '__main__':
    try:
        main()
        # print(f"get_uv = {get_uv('Hangzhou')}")
    except KeyboardInterrupt:
        log.log('个性化智能房屋硬件系统停止工作', 'exit')

