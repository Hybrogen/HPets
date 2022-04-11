
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

lightConf = HConfig.CONFIG(CONFS + '/light_conf', CONFS + '/light_conf_reset')
dhtConf = {
    'temperature': 24,
    'humidity': 60,
    'water_auto': True,
    'water_state': False,
    'heat_auto': True,
    'heat_state': False,
}
dhtConf = HConfig.CONFIG(CONFS + '/dht_conf', CONFS + '/dht_conf_reset', dhtConf)

def index(request):
    return HttpResponse('这不是你该来的地方')

############################## 设置系列 ##############################

def set_hconfig(change_info: dict) -> bool:
    with open('HModules/thresholds', encoding='utf8') as f: hconfig = json.loads(f.readline())
    for k, v in change_info.items():
        if k in hconfig: hconfig[k] = v
    with open('HModules/thresholds_reset', 'w', encoding='utf8') as f: f.write(json.dumps(hconfig))
    return True

def set_temperature(request):
    query_data = json.loads(request.body)
    rdata = dict()
    rdata['temperature'] = float(query_data['num'])
    set_hconfig(rdata)
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def set_humidity(request):
    query_data = json.loads(request.body)
    rdata = {'pid': query_data['houseNum']}
    rdata['humidity'] = int(query_data['num'])
    set_hconfig(rdata)
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def set_light(request):
    r"""
    POST request
    设置灯光配置，请求数据
    必须字段：
    houseNum -- 节点 id
    lightId -- 灯光配置 id
    非必须字段：
    name -- 灯光名
    local -- 灯光安置地点
    light -- 灯光亮度
    color -- 灯光颜色
    state -- 灯光状态 1 - 开，0 - 关
    """
    query_data = json.loads(request.body)
    rdata = {'pid': query_data['houseNum']}
    for newConf in query_data['setLights']:
        lightId = str(newConf['lightId'])
        conf = lightConf.get_data([lightId])
        for k in conf:
            if k in newConf:
                conf[k] = newConf[k]
    lightConf.save()
    rdata['config'] = lightConf.get_data()
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def set_water(request):
    query_data = json.loads(request.body)
    rdata = dict()
    rdata['water_auto'] = False
    rdata['water_state'] = bool(query_data['status'])
    set_hconfig(rdata)
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def set_curtain(request):
    query_data = json.loads(request.body)
    rdata = dict()
    rdata['curtain_auto'] = False
    rdata['curtain_state'] = bool(query_data['status'])
    set_hconfig(rdata)
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

############################## 获取系列 ##############################

def get_ports(request):
    rdata = {'ports': sql.get_ports()}
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def get_data(request):
    # print(f"get_data = {request.GET}")
    r"""
    GET request
    """
    rdata = dict()
    rdata['pid'] = request.GET['houseNum'][0]
    if 'startTime' in request.GET and 'endTime' in request.GET:
        rdata['start_date'] = request.GET['startTime']
        rdata['end_date'] = request.GET['endTime']
    else:
        rdata['start_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 24*3600))
        rdata['end_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    rdata['data_type'] = 'dht'
    dht_data = sql.get_data(rdata)
    # rdata['data_type'] = 'light'
    # light_data = sql.get_data(rdata)
    # return JsonResponse({'state': 'ok', 'dht_data': dht_data, 'light_data': light_data})
    return JsonResponse({'state': 'ok', 'dht_data': dht_data})

def get_light_config(request):
    r"""
    此函数用于返回灯光的配置数据

    Return value / exceptions raised:
    - 返回一个字典
    """
    rdata = {'pid': request.GET['houseNum'][0]}
    if not lightConf.data:
        lightFields = ['id', 'name', 'local', 'light', 'color', 'state']
        query_sql = f"""
        SELECT {', '.join(['`' + f + '`' for f in lightFields])}
        FROM `light_config` WHERE `pid` = {rdata['pid']}
        """
        lights = sql.sql_select(lightFields, query_sql)
        for light in lights:
            lid = light['id']
            del light['id']
            lightConf.updata(lid, light)
        # lightConf.save()
    rdata['lights'] = lightConf.get_data()
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def get_dht_config(request):
    r"""
    GET request
    此函数用于返回DHT传感器的配置数据

    Return value / exceptions raised:
    - 返回一个字典，内容是
    {
        "temperature": 27,
        "humidity": 44,
        "curtain_auto": true,
        "curtain_state": true,
        "water_auto": false,
        "water_state": false,
    }
    """
    rdata = dhtConf.get_data()
    rdata['pid'] = request.GET['houseNum'][0]
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def get_masters(request):
    r"""
    GET request
    返回已经登陆的人脸

    Return value / exceptions raised:
    - 返回一个列表 [{}, {},]
    """
    rdata = {'state': 'ok'}
    masters = [cam.get_user_info(userHeadPic[:-4]) for userHeadPic in os.listdir(FACES)]
    rdata['masters'] = masters
    return JsonResponse(rdata)

############################## 添加系列 ##############################

def add_port(request):
    r"""
    POST 请求:
    首先获取请求中的 name 和 local 字段插入添加一个节点
    之后查询最新的节点信息
    """
    qdata = json.loads(request.body)
    query_data = [qdata['portName'], qdata['portLocal']]
    # query_data = ['新', '奥秘客人']
    query_sql = "INSERT INTO `ports`(`name`, `local`) VALUES(%s, %s)"
    sql.sql_insert(query_sql, query_data)

    query_sql = "SELECT * FROM `ports` WHERE `id` = (SELECT MAX(`id`) FROM `ports`)"
    rdata = sql.sql_select(['id', 'name', 'local'], query_sql)[0]
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def add_light(request):
    r"""
    POST 请求:
    需要获取的字段:
    pid -- 节点 id【必须
    name -- 灯光名称备注【非必须
    local -- 灯光布置地点备注【非必须
    """
    qdata = json.loads(request.body)
    # qdata = {'pid':1 ,'name': '卧室主灯', 'local': '卧室'}
    insert_data = dict()
    for f in ['pid', 'name', 'local']:
        if qdata.get(f, None):
            insert_data[f] = qdata[f]
    query_sql = f"""
    INSERT INTO `light_config`({', '.join(['`' + f + '`' for f in insert_data.keys()])})
    VALUES({', '.join(['%s']*len(insert_data.keys()))})
    """
    sql.sql_insert(query_sql, list(insert_data.values()))

    query_sql = "SELECT * FROM `light_config` WHERE `id` = (SELECT MAX(`id`) FROM `light_config`)"
    rdata = sql.sql_select(['id', 'pid', 'name', 'local', 'light', 'color', 'state'], query_sql)[0]
    rdata['state'] = 'ok'
    return JsonResponse(rdata)

def add_master(request):
    r"""
    POST 注册新的房屋主人
    需要的字段：
    facePic -- 人脸的照片的 base64 编码字符串
    name -- 需要注册的照片的 id / 名字
    """
    qdata = json.loads(request.body)
    with open(f"{FACES}/{qdata['name']}.jpg", 'wb') as f:
        f.write(base64.b64decode(qdata['facePic']))
    cam.add_user(qdata['name'])
    rdata = cam.user_info(qdata['name'])
    return JsonResponse(rdata)

