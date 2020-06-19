from .. import models


class ACStateManager:

    def startAC(self, roomNumber):
        """
        生成空调实例，添加到数据库
        :param roomNumber: 要开启的空调房间号
        :return:
        """
        _AC = models.AC()
        _AC.init(roomNumber)
        _AC.save()
