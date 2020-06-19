class RespondPack(object):
    def __init__(self, status):
        self.status = status
        if status == 400:
            self.info = "Server not available(Server not exist or inited)"
        elif status == 401:
            self.info = "Server already initiated"
        elif status == 410:
            self.info = "Invalid arguments"
        elif status == 411:
            self.info = "Invalid roomNumber"
        elif status == 412:
            self.info = "room has already been taken"
        elif status == 413:
            self.info = "database transaction error"
        elif status == 414:
            self.info = "room is empty"
        elif status == 415:
            self.info = "ID mismatch"
        elif status == 200:
            self.info = "OK"

    def setInfo(self, info):
        self.info = info

    def keys(self):
        return 'status', 'info'

    def __getitem__(self, item):
        return getattr(self, item)


class DetailResponse(RespondPack):
    def __init__(self, status, detail):
        super().__init__(status)
        self.detail = detail

    def keys(self):
        return 'status', 'info', 'detail'


class UpdateResponse(RespondPack):
    def __init__(self, status, speed):
        super().__init__(status)
        self.speed = speed

    def keys(self):
        return 'status', 'info', 'speed'


