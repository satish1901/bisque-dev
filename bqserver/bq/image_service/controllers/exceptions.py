

class DataSrvException(object):
    pass

class UnsupportedFormat(DataSrvException):
    def __init__(self, fname):
        self.fname = fname

class UnknownService(DataSrvException):
    def __init__(self, fname):
        self.name = fname
    
class IllegalOperation(DataSrvException):
    def __init__(self, msg):
        self.msg = msg
