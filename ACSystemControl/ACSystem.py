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
    global server

    # executing result
    statusCode = 200

    if server is not None:
        statusCode = 401
    else:
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
        response = Response.RespondPack(statusCode)
        return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def register(request):
    """
    前台完成旅客登记

    返回码报错信息请查看 Response.py
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

    返回码报错信息请查看 Response.py
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

    返回码报错信息请查看 Response.py
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
    # ct -> currentTemperature  tt -> targetTemperature
    # cm -> currentMode         tm -> targetMode
    # cs -> currentSpeed        ts -> targetSpeed
    state = [request.GET.get("ct", default=None), request.GET.get("tt", default=None),
             request.GET.get("cm", default=None), request.GET.get("tm", default=None),
             request.GET.get("cs", default=None), request.GET.get("ts", default=None)]

    for item in state:
        if item is None:
            invalid = True
    if roomNumber is None or invalid:
        statusCode = 410
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        statusCode, speed = server.update(roomNumber, state)

    response = Response.UpdateResponse(statusCode, speed)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


# TODO powerOff 函数 和 hibernate函数
def powerOff(request):
    global server
    statusCode = 200

    roomNumber = request.GET.get("roomNumber", default=None)
    if roomNumber is None:
        statusCode = 411
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        status = server.cancel(roomNumber)

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")


def hibernate(request):
    global server
    statusCode = 200

    roomNumber = request.GET.get("roomNumber", default=None)
    if roomNumber is None:
        statusCode = 411
    elif server is None or server.status == "off":
        statusCode = 400
    else:
        status = server.hibernate(roomNumber)

    response = Response.RespondPack(statusCode)
    return HttpResponse(json.dumps(dict(response)), content_type="application/json")
