class RoomBindMapper:
    """
    RoomBindMapper
    维护入住信息
    """

    def __init__(self, num):
        """
        设想：房间数量小用list实现，房间数量大用dict实现
        TODO 性能优化 数量小使用list， 数量大使用dict
        :param num: 房间数量
        """
        self.upperBound = int(num)
        _roomBindDict = []
        for i in range(200):
            _roomBindDict.append(None)

        self.roomBindDict = _roomBindDict

    def register(self, roomNumber, ID):
        """
        登记入住信息
        :param roomNumber: 入住的房间号
        :param ID: 入住人的身份证号
        :return: 411    房间号越界
                 412    房间已经被占用
                 200    登记成功
        """
        statusCode = 200
        roomNumber = int(roomNumber)
        if roomNumber > self.upperBound or roomNumber <= 0:
            statusCode = 411
        elif self.roomBindDict[roomNumber - 1] is None:
            self.roomBindDict[roomNumber - 1] = ID
        elif self.roomBindDict[roomNumber - 1] is not None:
            statusCode = 412

        return statusCode

    def checkout(self, roomNumber, ID):
        """
        住户退房
        :param roomNumber:退房房号
        :param ID: 退房人ID
        :return: 411    房间号越界
                 414    房间是空房
                 415    入住人不匹配
                 200    退房成功
        """
        statusCode = 200
        roomNumber = int(roomNumber)
        if roomNumber > self.upperBound or roomNumber <= 0:
            statusCode = 411
        elif self.roomBindDict[roomNumber - 1] is None:
            statusCode = 413
        elif self.roomBindDict[roomNumber - 1] != ID:
            statusCode = 415
        else:
            # 退房
            self.roomBindDict[roomNumber - 1] = None

        return statusCode

    def query(self, roomNumber, ID):
        """
        查询入住信息
        :param roomNumber:
        :param ID:
        :return: statusCode 411 房间号越界
                            414 房间是空房
                            415 入住人不匹配
                            200 入住信息匹配
        """
        statusCode = None
        roomNumber = int(roomNumber)
        if roomNumber > self.upperBound or roomNumber <= 0:
            statusCode = 411
        elif self.roomBindDict[roomNumber] is None:
            statusCode = 413
        elif self.roomBindDict[roomNumber] != ID:
            statusCode = 415
        elif self.roomBindDict[roomNumber] == ID:
            statusCode = 200
        return statusCode
