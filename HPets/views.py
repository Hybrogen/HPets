
from asyncio import FastChildWatcher
from django.shortcuts import HttpResponse
from django.http import JsonResponse

import json
import time
import os

from HModules import HMySQL, HConfig,  HActuator

sql = HMySQL.HSQL('HHOME')
cam = HActuator.CAM()

MDIR = 'HModules'
FACES = MDIR + '/baseFaces'
if not os.path.isdir(FACES): os.mkdir(FACES)
CONFS = MDIR + '/conf'
if not os.path.isdir(CONFS): os.mkdir(CONFS)

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
homeConf = HConfig.CONFIG(CONFS + '/home_conf', CONFS + '/home_conf_reset', homeConf)

def index(request):
    return HttpResponse('这不是你该来的地方')

############################## 设置系列 ##############################

def set_all(request):
    try:
        qdata = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        qdata = dict()
    for k in homeConf.get_data().keys():
        if k in qdata:
            homeConf.data[k] = qdata[k]
    homeConf.save(reset = True)
    return JsonResponse(homeConf.get_data())

############################## 获取系列 ##############################

def get_sensors(request):
    homeConf.load()
    rdata = homeConf.get_data()
    # rdata['food'] = rdata['left_food']
    # del rdata['left_food']
    # rdata['water'] = rdata['left_water']
    # del rdata['left_water']
    return JsonResponse(rdata)

# def get_pet_sleep(request):
#     rdata = dhtConf.get_data()
#     rdata['pid'] = request.GET['houseNum'][0]
#     rdata['state'] = 'ok'
#     return JsonResponse(rdata)
#     
#     rdata = dict()
#     rdata['pid'] = request.GET['houseNum'][0]
#     if 'startTime' in request.GET and 'endTime' in request.GET:
#         rdata['start_date'] = request.GET['startTime']
#         rdata['end_date'] = request.GET['endTime']
#     else:
#         rdata['start_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 24*3600))
#         rdata['end_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
#     rdata['data_type'] = 'pett'
#     pett_data = sql.get_data(rdata)
#     i = 0
#     while pett_data[i]['pett'] < 20: i += 1
#     pett_data = pett_data[i:]
#     i = 0
#     while pett_data[i]['pett'] >= 20: i += 1
#     pett_data = pett_data[:i]
#     return JsonResponse({'state': 'ok', 'sleep_times': pett_data})

