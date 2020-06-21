from django.db import models
from datetime import datetime


class AC(models.Model):
    roomNumber = models.IntegerField(primary_key=True)
    status = models.CharField(max_length=10)
    currentSpeed = models.IntegerField()
    targetSpeed = models.IntegerField()
    targetTemperature = models.FloatField()
    currentTemperature = models.FloatField()
    waitTime = models.FloatField()

    def __str__(self):
        return str(self.roomNumber) + \
               ": mode " + str(self.currentMode) + \
               ", speed " + str(self.currentSpeed)

    def init(self, roomNumber):
        self.roomNumber = int(roomNumber)
        self.status = "off"
        self.currentSpeed = 0
        self.targetSpeed = 0
        self.currentTemperature = 0
        self.targetTemperature = 0
        self.waitTime = 0

    def addWaitTime(self, waitTime):
        self.waitTime += waitTime

    def stopServing(self):
        _record = Record()
        _record.init_ScheduleRecord(self, 0)
        self.currentSpeed = 0

        _record.save()
        self.save()

    def startServing(self):
        _record = Record()
        _record.init_ScheduleRecord(self, self.targetSpeed)
        self.currentSpeed = self.targetSpeed

        _record.save()
        self.save()

    def isNewRequest(self, state, status):
        """
        根据用户端上传的目标温度和目标风速是否和数据库中的匹配判断是否是一个新的请求
        :param state 请求
        :param status 状态
        :return 0 关机
                1 开机
                2 休眠
                3 调风调温
                4 没变化
        """
        # 空调状态发生变化之后产生的新请求
        if self.status != status:
            if status == "powerOff":
                return 0
            elif status == "on":
                return 1
            elif status == "hibernate":
                return 2
        # 仅仅是调风和调温度
        else:
            if self.targetTemperature != state[1] or self.targetSpeed != state[3]:
                return 3
            else:
                return 4

    def update(self, state, status):
        """
        用当前状态更新数据库
        :param state: 空调运行参数
        :param status: 空调状态
        :return:
        """

        # 根据数据是否被改变产生相应的记录
        statusModified = False
        targetTemperatureModified = False
        targetSpeedModified = False

        # 目标温度改变——>用户调温
        if self.targetTemperature != state[1]:
            targetTemperatureModified = True
        # 目标风速改变——>用户调风
        if self.targetSpeed != state[3]:
            targetSpeedModified = True
        # 状态改变-->用户开关机/空调休眠
        if self.status != status:
            statusModified = True

        # 用户开关机/空调休眠
        if statusModified:
            _record = Record()
            _record.init_OperationRecord()
            _record.save()

        # 用户调风调温
        # 默认不修改
        new_targetTemperature = -1
        new_targetSpeed = -1

        if targetSpeedModified:
            new_targetSpeed = state[3]
        if targetTemperatureModified:
            new_targetTemperature = state[1]

        _record = Record()
        _record.init_RequestRecord(self, new_targetTemperature, new_targetSpeed)
        _record.save()

        self.currentTemperature = state[0]
        self.targetSpeed = state[3]
        self.targetTemperature = state[1]
        self.status = status
        self.save()


class Record(models.Model):
    ac = models.ForeignKey(AC, on_delete=models.CASCADE)

    # 调温度
    last_targetTemperature = models.IntegerField()
    new_targetTemperature = models.IntegerField()

    # 调风速
    last_targetSpeed = models.IntegerField()
    new_targetSpeed = models.IntegerField()

    # 送风
    old_speed = models.IntegerField()
    new_speed = models.IntegerField()

    # 操作
    old_status = models.CharField(max_length=10)
    new_status = models.CharField(max_length=10)

    date = models.DateTimeField()

    def __str__(self):
        return "record : " \
               "targetTemperature from " + str(self.last_targetTemperature) + " to " + str(self.new_targetTemperature) + ", " \
               "targetSpeed from " + str(self.last_targetSpeed) + " to " + str(self.new_targetSpeed) + ", " \
               "speed from " + str(self.old_speed) + " to " + str(self.new_speed)

    def init_OperationRecord(self, ac, new_status):
        """
        创建一条关于用户/系统操作的记录
        :param new_status: 新的空调状态
        :return:
        """
        self.ac = ac
        self.old_speed = ac.currentSpeed
        self.new_speed = ac.currentSpeed
        self.last_targetTemperature = ac.targetTemperature
        self.new_targetTemperature = ac.targetTemperature
        self.last_targetSpeed = ac.targetSpeed
        self.new_targetSpeed = ac.targetSpeed
        self.date = datetime.now()

        self.old_status = ac.status
        self.new_status = new_status

    def init_RequestRecord(self, ac, new_targetTemperature, new_targetSpeed):
        """
        创建一条关于请求的记录
        :param ac: 空调
        :param new_targetTemperature 请求温度
        :param new_targetSpeed  请求风速
        :return:
        """

        assert new_targetTemperature != -1 or new_targetSpeed != -1
        self.ac = ac
        _AC = self.ac
        self.old_speed = _AC.currentSpeed
        self.new_speed = _AC.currentSpeed
        self.old_status = _AC.status
        self.new_status = _AC.status
        self.last_targetTemperature = _AC.targetTemperature
        self.last_targetSpeed = _AC.targetSpeed
        self.date = datetime.now()

        if new_targetSpeed != -1:
            self.new_targetSpeed = new_targetSpeed
        else:
            self.new_targetSpeed = _AC.targetSpeed

        if new_targetTemperature != -1:
            self.new_targetTemperature = new_targetTemperature
        else:
            self.new_targetTemperature = _AC.targetTemperature

    def init_ScheduleRecord(self, ac, new_speed):
        self.ac = ac
        self.old_speed = ac.currentSpeed
        self.last_targetTemperature = ac.targetTemperature
        self.last_targetSpeed = ac.targetSpeed
        self.new_targetTemperature = ac.targetTemperature
        self.new_targetSpeed = ac.targetSpeed

        self.new_speed = new_speed

    def toFile(self):
        _AC = self.ac
        _list = [str(_AC.roomNumber),
                 str(self.old_speed), str(self.new_speed),
                 str(self.last_targetSpeed), str(self.new_targetSpeed),
                 str(self.last_targetTemperature), str(self.new_targetTemperature),
                 str(self.date)]
        record_file = " ".join(_list)
        return record_file
