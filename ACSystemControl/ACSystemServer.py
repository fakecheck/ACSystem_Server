import queue
import threading

from . import models
from .Modules.StatManager import StatManager
from .Modules.RoomBindMapper import RoomBindMapper
from .Modules.ACBillingManager import ACBillingManager
from .Modules.ACStateManager import ACStateManager
from .Modules.Scheduler import ACAirRequest, PriorityScheduler, RoundScheduler


class DefaultSetting:
    INSTANCE_NUM = 3
    AC_START_UP_TEMPERATURE = 25
    AC_START_UP_TARGET_TEMPERATURE = 25
    AC_START_UP_MODE = 1
    AC_START_UP_SPEED = 1


class Config:
    """
    空调服务的运行配置
    """

    def __init__(self, setting):
        self.instanceNum = setting.INSTANCE_NUM


class ACServer:
    def __init__(self, setting):
        # modules
        self.ACStateManager = None
        self.RoomBindMapper = None
        self.ACBillingManager = None
        self.StatManager = None
        self.priorityScheduler = None
        self.roundScheduler = None

        # Request Queue Resources
        self.RequestQueue = None
        self.RequestQueueLock = threading.Lock()
        self.RequestQueueNotEmptyEvent = threading.Event()

        # server setting
        self.SETTING = setting
        self.roomNum = setting.roomNum

        self.status = "off"

    def startup(self):
        self.status = "on"

        self.RoomBindMapper = RoomBindMapper(self.roomNum)
        self.ACStateManager = ACStateManager()
        self.ACBillingManager = ACBillingManager()
        self.StatManager = StatManager()

        self.RequestQueue = queue.Queue()
        self.priorityScheduler = PriorityScheduler(self.SETTING.INSTANCE_NUM,
                                                   self.RequestQueue,
                                                   self.RequestQueueLock,
                                                   self.RequestQueueNotEmptyEvent)

    def register(self, roomNumber, ID):
        """
        登记入住信息
        :param roomNumber: 入住的房间号
        :param ID: 入住人的身份证号
        :return: 411    房间号越界
                 412    房间已经被占用
                 413    数据库添加出错
                 200    登记成功
        """
        statusCode = self.RoomBindMapper.register(roomNumber, ID)
        if statusCode != 200:
            return statusCode
        try:
            self.ACStateManager.startAC(roomNumber)
        except:
            statusCode = 413
        return statusCode

    def checkout(self, roomNumber, ID):
        """
        住户离店
        :param roomNumber: 退房房间号
        :param ID: 退房身份证号码
        :return: 411    房间号越界
                 414    房间是空房
                 415    入住人不匹配
                 413    数据库出错
                 200    退房成功
        """
        status = self.RoomBindMapper.checkout(roomNumber, ID)
        if status != 200:
            return status

        # 删除房间实例，并且将使用记录实例化
        # TODO : 后续经理报表还需要统计用户修改的次数，
        #  所以后面这个地方还要加上用户操作的统计
        try:
            _AC = models.AC.objects.get(roomNumber=roomNumber)
            records = models.Record.objects.filter(ac=_AC)
            with open('Usage.log', 'a+') as f:
                for item in records:
                    record_file = item.toFile()
                    f.write(record_file)

            _AC.delete()
        except:
            status = 413

        return status

    def checkDetail(self, roomNumber, ID):
        statusCode = self.RoomBindMapper.query(roomNumber, ID)
        if statusCode != 200:
            return statusCode, None
        # TODO 详单生成
        detail = self.ACBillingManager.query(roomNumber)
        return statusCode, detail

    def update(self, roomNumber, state):
        """
        TODO 写注释
        :param roomNumber:
        :param state:
        :return:
        """
        statusCode = 200
        speed = 0
        _AC = None
        try:
            _AC = models.AC.objects.get(roomNumber=roomNumber)
        except:
            statusCode = 411

        if statusCode == 200:
            if _AC.isNewRequest(state):
                airRequest = ACAirRequest(roomNumber, state[1], state[5])

                self.RequestQueueLock.acquire()
                # 目前没有请求， 那么还需要把调度器给打开
                if self.RequestQueue.qsize() == 0:
                    self.RequestQueue.put(airRequest)
                    self.RequestQueueNotEmptyEvent.set()
                # 已经有请求了就直接加入队列
                else:
                    self.RequestQueue.put(airRequest)

                self.RequestQueueNotEmptyEvent.set()
                self.RequestQueueLock.release()

            # update database
            _AC = models.AC.objects.get(roomNumber=roomNumber)
            _AC.update(state)

            # update client current wind speed
            speed = _AC.currentSpeed

        return statusCode, speed

    def powerOff(self, roomNumber):
        statusCode = 200

        _AC = None
        try:
            _AC = models.AC.objects.get(roomNumber=roomNumber)
        except:
            statusCode = 411

        if statusCode == 200:
            self.priorityScheduler.cancel(roomNumber)

    def hibernate(self, roomNumber):
        pass

