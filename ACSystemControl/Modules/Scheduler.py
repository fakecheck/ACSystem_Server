import threading
from datetime import datetime
from ..models import AC, Record


class Request:
    """
    请求对立中的请求
    :arg type "on" 开机请求/送风请求
              "powerOff" 关机请求
              "hibernate" 休眠请求

    """
    def __init__(self):
        self.airRequest = None
        self.type = None

    def setAirRequest(self, airRequest):
        self.airRequest = airRequest

    def setType(self, type):
        self.type = type


class ACAirRequest:
    """
    送风请求
    :param roomNumber 房间号码
    :param targetTemperature 目标温度
    :param targetSpeed 目标风速
    :param lastWaitStartTime 开始等待的时间
    :param waitingTime 总共等待的时间
    """

    def __init__(self, roomNumber, targetTemperature, targetSpeed):
        self.roomNumber = roomNumber
        self.targetTemperature = targetTemperature
        self.targetSpeed = targetSpeed
        self.lastWaitStartTime = datetime.now()
        self.waitingTime = None

    def getWaitTime(self):
        """
        返回等待时间
        :return:
        """
        _current_time = datetime.now()

        if self.waitingTime is None:
            waitTime = _current_time - self.lastWaitStartTime
        else:
            waitTime = _current_time - self.lastWaitStartTime
            waitTime += self.waitingTime

        return waitTime

    def startWaiting(self):
        """
        该Request开始等待
        :return:
        """
        self.lastWaitStartTime = datetime.now()

    def stopWaiting(self):
        """
        该Request停止等待
        :return:
        """
        self.waitingTime = datetime.now() - self.lastWaitStartTime
        self.lastWaitStartTime = None

    def setWaitTime(self, waitTime):
        """
        设置已经等待的时长
        :param waitTime:
        :return:
        """
        self.waitingTime = waitTime


class ServingInstance:
    """
    服务对象
    :param number 服务对象编号
    """
    def __init__(self, number):
        self.number = number
        self.airRequest = None
        self.servingTimeStamp = None
        # TODO 功能拓展 可以拓展服务对象的属性

    def serve(self, airRequest):
        """
        为一个送风请求开始服务
        记录服务时间
        :param airRequest: 送风请求
        :return:
        """
        self.airRequest = airRequest
        self.servingTimeStamp = datetime.now()


class ServingCluster:
    """
    服务对象集群
    :param instanceNum 服务对象数量
    :parameter runningInstance 正在运行的服务对象数量
    """
    def __init__(self, instanceNum):
        self.instanceNum = instanceNum
        self.instances = []
        for i in range(instanceNum):
            self.instances.append(ServingInstance(i))
        self.runningInstance = 0

    def canServe(self):
        """
        服务对象集群是否可以接受新的请求
        :return:
        """
        if self.runningInstance < self.instanceNum:
            return True
        else:
            return False

    def serve(self, airRequest):
        """
        处理一个送风请求
        :param airRequest:
        :return:
        """
        airRequest.stopWaiting()
        self.runningInstance += 1
        for i in range(self.instanceNum):
            if self.instances[i].airRequest is None:
                self.instances[i].serve(airRequest)
                break

    def quitServing(self, num):
        """
        停止服务一个请求
        （主要由调度触发，送风请求并没有被满足，而是因为优先级问题被调出）
        :param num: 停止运行在几号服务对象上的服务
        :return: airRequest 被调出的送风请求
        """
        self.runningInstance -= 1
        airRequest = self.instances[num].airRequest
        self.instances[num].airRequest = None

        airRequest.startWaiting()
        return airRequest

    def finishServing(self, roomNumber):
        """
        完成了一个请求
        （主要由取消触发，送风请求已经被满足）
        :param roomNumber: 停止服务的房间号
        :return: airRequest 被满足的请求
        """
        self.runningInstance -= 1
        airRequest = None
        for idx, item in enumerate(self.instances):
            if item.airRequest.roomNumber == roomNumber:
                airRequest = self.instances[idx].airRequest
                self.instances[idx].airRequest = None

        return airRequest

    def updateRequest(self, newRequest):
        for idx, item in enumerate(self.instances):
            if item.airRequest.roomNumber == newRequest.roomNumber:
                self.instances[idx].airRequest = newRequest
                break

    def getServingStatus(self):
        """
        获取当前服务对象集群的服务状态简报
        :return: servingSpeedList 服务对象集群上的送风速度
                 servingTimeList 服务对象集群上的送风时长
        """
        servingSpeedList = []
        servingTimeList = []
        for item in self.instances:
            if item.airRequest is not None:
                servingSpeedList.append(item.airRequest.targetSpeed)
                servingTimeList.append(datetime.now() - item.servingTimeStamp)
            else:
                servingSpeedList.append(0)
                servingTimeList.append(None)

        return servingSpeedList, servingTimeList

    def getRoomNumbers(self):
        _list = []
        for item in self.instances:
            _list.append(item.airRequest.roomNumber)
        return _list

class Scheduler:
    """
    调度器基类
    :param cluster 服务对象集群
    :param instanceNum 服务对象数量
    """
    # 共有属性 三个队列
    lowSpeedQueue = []
    midSpeedQueue = []
    highSpeedQueue = []

    def __init__(self, instanceNum, cluster):
        self.instanceNum = instanceNum
        self.cluster = cluster


class PriorityScheduler(threading.Thread, Scheduler):
    """
    优先级调度器
    有新请求的时候产生跟据优先级进行调度
    :param instanceNum Scheduler父类-服务对象数量
    :param cluster Scheduler父类-服务对象集群
    :param requestQueue 请求队列——客户端的消息队列
    因为请求队列是调度器和客户端共同使用的，下面的两个资源是用来进程之间同步的
    :param lock 请求队列加的锁
    :param event 请求队列有新请求的事件
    """
    def __init__(self, instanceNum, cluster, requestQueue, lock, event):
        Scheduler.__init__(self, instanceNum, cluster)
        threading.Thread.__init__(self)

        # request queue resource
        self.requestQueue = requestQueue
        self.lock = lock
        self.event = event

    def canSchedule(self):
        """
        判断当前状态是否可以进行调度
        :return: 2 可以直接接受新请求
                 1 可以进行优先级调度
                 0 没办法调度
        """
        # 如果有空闲的服务对象
        if self.cluster.canServe():
            return 2
        else:
            # 查看当前服务的优先级，是否有低于正在等待的请求
            speedList = self.cluster.getServingStatus()
            minServingSpeed = 4
            for item in speedList:
                if item < minServingSpeed:
                    minServingSpeed = item

            maxWaitingSpeed = 0
            if len(self.highSpeedQueue) > 0:
                maxWaitingSpeed = 3
            elif len(self.midSpeedQueue) > 0:
                maxWaitingSpeed = 2
            elif len(self.lowSpeedQueue) > 0:
                maxWaitingSpeed = 1

            if minServingSpeed < maxWaitingSpeed:
                return 1
            else:
                return 0

    def getRequest(self):
        """
        获取一个优先级最高的请求
        :return:  airRequest 优先级最高的请求
        """
        airRequest = None
        if len(self.highSpeedQueue) > 0:
            airRequest = self.highSpeedQueue.pop(0)
        elif len(self.midSpeedQueue) > 0:
            airRequest = self.midSpeedQueue.pop(0)
        elif len(self.lowSpeedQueue) > 0:
            airRequest = self.lowSpeedQueue.pop(0)
        return airRequest

    def putRequest(self, airRequest):
        """
        将一个请求放入等待队列
        :param airRequest:
        :return:
        """
        # 请求开始等待
        airRequest.startWaiting()

        # 放入相应队列
        if airRequest.targetSpeed == "1":
            self.lowSpeedQueue.append(airRequest)
        elif airRequest.targetSpeed == "2":
            self.midSpeedQueue.append(airRequest)
        elif airRequest.targetSpeed == "3":
            self.highSpeedQueue.append(airRequest)

    def schedule(self):
        """
        进行调度
        :return:
        """
        while True:
            canSchedule = self.canSchedule()
            if canSchedule == 0:
                # 无法调度 已经最优了
                break
            elif canSchedule == 2:
                # 有空位直接服务
                airRequest = self.getRequest()
                self.cluster.serve(airRequest)
            elif canSchedule == 1:
                # 进行优先级调度
                speedList, IGNORE = self.cluster.getServingStatus()

                minServingSpeed = 4
                minServingSpeedIndex = 0
                for idx, item in enumerate(speedList):
                    if item < minServingSpeed:
                        minServingSpeed = item
                        minServingSpeedIndex = idx

                # 淘汰优先级最低的送风请求（风速最小），放回等待队列
                ms_airRequest = self.cluster.quitServing(minServingSpeedIndex)
                self.putRequest(ms_airRequest)
                # 更新空调状态
                _AC = AC.objects.get(roomNumber=ms_airRequest.roomNumber)
                _AC.stopServing()

                # 获得优先级最高的送风请求（风速最大），开始服务
                airRequest = self.getRequest()
                self.cluster.serve(airRequest)
                # 更新空调状态
                _AC = AC.objects.get(roomNumber=airRequest.roomNumber)
                _AC.startServing()

    def run(self):
        """
        运行
        :return:
        """
        while True:
            # 如果 队列中没有请求的话，就挂起，避免一直占用锁资源（拿了放， 放了拿）
            if len(self.requestQueue) == 0:
                self.event.wait()
                if self.event.isSet():
                    self.event.clear()

            # 处理请求
            self.lock.acquire()
            request = self.requestQueue.pop(0)
            self.lock.release()

            # 如果是关机，或者休眠，直接取消送风请求
            if request.type == "off" or request.type == "hibernate":
                waitTime = self.cancel(request.airRequest)
                waitTime = waitTime.seconds/60
                _AC = AC.objects.get(roomNumber=request.airRequest)
                _AC.addWaitTime(waitTime)
                _AC.save()

            else:
                # 判断该房间是否有请求在队列中
                _request, serving = self.findRequest(request.airRequest.roomNumber)
                # 该房间没有请求在队列中/服务中
                if _request is None:
                    # 构造新请求，放入队列
                    airRequest = request.airRequest
                    self.putRequest(airRequest)
                # 该房间有请求在队列中，正在等待，或者正在送风
                else:
                    self.updateRequest(_request, request, serving)

            # 调度
            self.schedule()

    def updateRequest(self, oldRequest, newRequest, serving):
        """
        更新请求
        如果被更新的请求正在被服务，直接更新请求即可
        如果被更新的请求正在等待，如果新请求没有更改风速，则不改变请求位置（不需要重新排队），只修改风速
                            如果新请求更改了风速，则需要对更改了风速的请求重新排队
        :param oldRequest:  旧请求
        :param newRequest:  新请求
        :param serving:     旧的请求是否正在被服务
        :return:
        """
        if serving:
            self.cluster.updateRequest(newRequest)
        else:
            # 只是调温，没有改变风速
            if oldRequest.targetSpeed == newRequest.targetSpeed:
                if oldRequest.targetSpeed == 1:
                    # 低风
                    for idx, item in enumerate(self.lowSpeedQueue):
                        if item.roomNumber == oldRequest.roomNumber:
                            self.lowSpeedQueue[idx] = newRequest
                elif oldRequest.targetSpeed == 2:
                    # 中风
                    for idx, item in enumerate(self.midSpeedQueue):
                        if item.roomNumber == oldRequest.roomNumber:
                            self.midSpeedQueue[idx] = newRequest
                elif oldRequest.targetSpeed == 3:
                    # 高风
                    for idx, item in enumerate(self.highSpeedQueue):
                        if item.roomNumber == oldRequest.roomNumber:
                            self.highSpeedQueue[idx] = newRequest
            # 改变了风速
            else:
                waitTime = self.cancel(oldRequest.roomNumber)
                newRequest.setWaitTime(waitTime)
                self.putRequest(newRequest)

    def findRequest(self, roomNumber):
        """
        查询送风请求
        :param roomNumber: 房间号
        :return: request    查找到的请求
                 serving    是否正在服务
        """
        request = None
        serving = False
        for item in self.lowSpeedQueue:
            if item.roomNumber == roomNumber:
                request = item
        for item in self.midSpeedQueue:
            if item.roomNumber == roomNumber:
                request = item
        for item in self.highSpeedQueue:
            if item.roomNumber == roomNumber:
                request = item
        for item in self.cluster.getRoomNumbers:
            if item.roomNumber == roomNumber:
                request = item
                serving = True
        return request, serving

    def cancel(self, roomNumber):
        """
        取消请求
        :param roomNumber: 取消请求的房间号
        :return: 被取消的请求总共的等待时长
        """
        request = None
        for idx, item in enumerate(self.lowSpeedQueue):
            if item.roomNumber == roomNumber:
                request = self.lowSpeedQueue[idx]
                self.lowSpeedQueue[idx] = None
        for idx, item in enumerate(self.midSpeedQueue):
            if item.roomNumber == roomNumber:
                request = self.midSpeedQueue[idx]
                self.midSpeedQueue[idx] = None
        for idx, item in enumerate(self.highSpeedQueue):
            if item.roomNumber == roomNumber:
                request = self.highSpeedQueue[idx]
                self.highSpeedQueue[idx] = None

        _request = self.cluster.finishServing(roomNumber)
        if _request is not None:
            request = _request

        request.stopWaiting()
        return request.getWaitTime()


class RoundScheduler(Scheduler):
    pass

