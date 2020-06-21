from django.http.response import HttpResponse
import json
from . import ACSystemServer, Response

SETTING = ACSystemServer.DefaultSetting()
server = None


def startup(request):
    """
    启动空调系统
    :param request:
    :return:

    返回码报错信息请查看 Response.py
    """
    global server, SETTING

    # executing result
    statusCode = 200

    # 服务器只是关闭了
    if server is not None and server.status == "off":
        server.status = "on"
    # 没有服务器
    elif server is None:
        roomNum = request.GET.get('roomNum', default=None)
        instanceNum = request.GET.get('instanceNum', default=None)
        if roomNum is not None:
            SETTING.roomNum = roomNum
        if instanceNum is not None:
            SETTING.INSTANCE_NUM = instanceNum

        if not hasattr(SETTING, "roomNumber"):
            statusCode = 410

        if statusCode != 200:
            response = Response.RespondPack(statusCode)
            return HttpResponse(json.dumps(dict(response)), content_type="application/json")

        server = ACSystemServer.ACServer(SETTING)
        server.startup()
    # 有服务器而且还开着
    elif server is not None and server.status == "on":
        statusCode = 401

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def shutdown(request):
    """
    关闭服务器，但是保留了服务器配置
    :param request:
    :return:
    """
    global server

    statusCode = 200
    server.status = "off"
    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def destroy(request):
    """
    彻底关闭服务器，不保留服务器配置，下次需要重新初始化
    :param request:
    :return:
    """
    global server

    statusCode = 200
    del server
    server = None
    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def config(request):
    """
    更改服务器配置
    :param request:
    :return:
    """
    global server, SETTING

    statusCode = 200
    mode = request.GET.get("mode", default=None)
    temperatureUpperBound = request.GET.get("ub", default=None)
    temperatureLowerBound = request.GET.get("lb", default=None)

    if mode == "cooling":
        if temperatureLowerBound is not None:
            SETTING.COOLING_WORK_TEMPERATURE_LOWERBOUND = temperatureLowerBound
        if temperatureUpperBound is not None:
            SETTING.COOLING_WORK_TEMPERATURE_UPPERBOUND = temperatureUpperBound

        SETTING.WORK_TEMPERATURE_UPPERBOUND = SETTING.COOLING_WORK_TEMPERATURE_UPPERBOUND
        SETTING.WORK_TEMPERATURE_LOWERBOUND = SETTING.COOLING_WORK_TEMPERATURE_LOWERBOUND

    elif mode == "heating":
        if temperatureLowerBound is not None:
            SETTING.HEATING_WORK_TEMPERATURE_LOWERBOUND = temperatureLowerBound
        if temperatureUpperBound is not None:
            SETTING.HEATING_WORK_TEMPERATURE_UPPERBOUND = temperatureUpperBound

        SETTING.WORK_TEMPERATURE_UPPERBOUND = SETTING.HEATING_WORK_TEMPERATURE_UPPERBOUND
        SETTING.WORK_TEMPERATURE_LOWERBOUND = SETTING.HEATING_WORK_TEMPERATURE_LOWERBOUND

    else:
        statusCode = 410

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def register(request):
    """
    前台完成旅客登记
    :param request:
    :return:
    """
    global server
    statusCode = 200
    roomNumber = request.GET.get("roomNumber", default=None)
    ID = request.GET.get("ID", default=None)
    if roomNumber is None or ID is None:
        statusCode = 410
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        statusCode = server.register(roomNumber, ID)

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def checkout(request):
    """
    前台办理用户退房手续
    :param request:
    :return:
    """
    global server
    statusCode = 200
    roomNumber = request.GET.get("roomNumber", default=None)
    ID = request.GET.get("ID", default=None)

    if roomNumber is None or ID is None:
        statusCode = 410
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        statusCode = server.checkout(roomNumber, ID)

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def checkDetail(request):
    """
    前台查询用户使用详单
    :param request:
    :return:
    """
    global server
    statusCode = 200
    detail = None

    roomNumber = request.GET.get("roomNumber", default=None)
    ID = request.GET.get("ID", default=None)

    if roomNumber is None or ID is None:
        statusCode = 410
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        statusCode, detail = server.checkDetail(roomNumber, ID)

    response = Response.DetailResponse(statusCode, detail)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def update(request):
    """
    处理客户的请求包/心跳包

    返回码报错信息请查看 Response.py
    :param request:
    :return:
    """
    global server
    statusCode = 200
    speed = 0

    invalid = False
    roomNumber = request.GET.get("roomNumber", default=None)
    status = request.GET.get("status", default=None)
    # ct -> currentTemperature  tt -> targetTemperature
    # cs -> currentSpeed        ts -> targetSpeed
    state = [request.GET.get("ct", default=None), request.GET.get("tt", default=None),
             request.GET.get("cs", default=None), request.GET.get("ts", default=None)]

    for item in state:
        if item is None:
            invalid = True
    if roomNumber is None or status is None or invalid:
        statusCode = 410
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        statusCode, speed = server.update(roomNumber, state, status)

    response = Response.UpdateResponse(statusCode, speed)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")
