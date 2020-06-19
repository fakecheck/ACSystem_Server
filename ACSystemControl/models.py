from django.db import models
from datetime import datetime


class AC(models.Model):
    roomNumber = models.IntegerField(primary_key=True)
    status = models.CharField(max_length=10)
    currentMode = models.IntegerField()
    targetMode = models.IntegerField()
    currentSpeed = models.IntegerField()
    targetSpeed = models.IntegerField()
    targetTemperature = models.FloatField()
    currentTemperature = models.FloatField()

    def __str__(self):
        return str(self.roomNumber) + \
               ": mode " + str(self.currentMode) + \
               ", speed " + str(self.currentSpeed)

    def init(self, roomNumber):
        self.roomNumber = int(roomNumber)
        self.status = "off"
        self.currentMode = 0
        self.targetMode = 0
        self.currentSpeed = 0
        self.targetSpeed = 0
        self.currentTemperature = 0
        self.targetTemperature = 0

    def setAC(self, state):
        self.targetTemperature = state[0]
        self.currentTemperature = state[1]
        self.currentMode = state[3]
        self.targetMode = state[3]
        self.targetSpeed = state[4]
        self.currentSpeed = state[5]

    def stopServing(self):
        _record = Record()
        _record.init(self, -1, 0)
        self.currentSpeed = 0

        _record.save()
        self.save()

    def startServing(self):
        _record = Record()
        _record.init(self, -1, self.targetSpeed)
        self.currentSpeed = self.targetSpeed

        _record.save()
        self.save()

    def isNewRequest(self, state):
        if self.targetTemperature != state[1] or self.targetSpeed != state[5]:
            return True
        else:
            return False

    def update(self, state):
        """
        update database with current Temperature and mode
        :param state:
        :return:
        """

        modeModified = False
        targetTemperatureModified = False
        targetSpeedModified = False

        if self.targetTemperature != state[1]:
            targetTemperatureModified = True
        if self.currentMode != state[3]:
            modeModified = True
        if self.targetSpeed != state[5]:
            targetSpeedModified = True

        new_mode = -1
        new_speed = -1
        new_targetTemperature = -1
        new_targetSpeed = -1

        if modeModified:
            new_mode = state[3]
        if targetSpeedModified:
            new_targetSpeed = state[5]
        if targetTemperatureModified:
            new_targetTemperature = state[1]

        _record = Record()
        _record.init(self, new_mode, new_speed, new_targetTemperature, new_targetSpeed)
        _record.save()

        self.currentTemperature = state[0]
        self.currentMode = state[3]
        self.targetMode = state[3]
        self.targetSpeed = state[5]
        self.targetTemperature = state[1]


class Record(models.Model):
    ac = models.ForeignKey(AC, on_delete=models.CASCADE)

    # 调模式
    old_mode = models.IntegerField()
    new_mode = models.IntegerField()

    # 调温度
    last_targetTemperature = models.IntegerField()
    new_targetTemperature = models.IntegerField()

    # 调风速
    last_targetSpeed = models.IntegerField()
    new_targetSpeed = models.IntegerField()

    # 送风
    old_speed = models.IntegerField()
    new_speed = models.IntegerField()

    date = models.DateTimeField()

    def __str__(self):
        return "record : " \
               "mode from " + str(self.old_mode) + " to " + str(self.new_mode) + ", " \
               "targetTemperature from " + str(self.last_targetTemperature) + " to " + str(self.new_targetTemperature) + ", " \
               "targetSpeed from " + str(self.last_targetSpeed) + " to " + str(self.new_targetSpeed) + ", " \
               "speed from " + str(self.old_speed) + " to " + str(self.new_speed)

    def init(self, ac, new_mode, new_speed, new_targetTemperature, new_targetSpeed):
        """
        创建一条记录

        :param ac: 属于哪个空调
        :param new_mode: 新的模式 如果是-1表示维持不变
        :param new_speed: 新的送风速度 如果是-1表示维持不变
        :param new_targetSpeed:  新的请求风速 如果是-1表示维持不变
        :param new_targetTemperature: 新的请求温度 如果是-1表示维持不变
        :return:
        """
        if new_speed == -1 and new_mode == -1:
            raise Exception("new_speed and new_mode Cannot be -1 at the same time")
        self.ac = ac

        # 模式更改
        self.old_mode = ac.currentMode
        if new_mode == -1:
            self.new_mode = ac.currentMode
        else:
            self.new_mode = new_mode

        # 送风状态更改
        self.old_speed = ac.currentSpeed
        if new_speed == -1:
            self.new_speed = ac.currentSpeed
        else:
            self.new_speed = new_speed

        # 调温
        self.last_targetSpeed = ac.targetSpeed
        if new_targetSpeed == -1:
            self.new_targetSpeed = ac.targetSpeed
        else:
            self.new_targetSpeed = new_targetSpeed

        # 调风
        self.last_targetTemperature = ac.targetTemperature
        if new_targetTemperature == -1:
            self.new_targetTemperature = ac.targetTemperature
        else:
            self.new_targetTemperature = new_targetTemperature

        self.date = datetime.now()

    def toFile(self):
        _AC = self.ac
        _list = [str(_AC.roomNumber), str(self.old_speed),
                 str(self.new_speed), str(self.old_mode),
                 str(self.new_mode), str(self.date)]
        record_file = " ".join(_list)
        return record_file
