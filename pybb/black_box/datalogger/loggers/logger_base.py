from abc import abstractmethod

class LoggerBase(object):
    @abstractmethod
    def log_data(self, variable, timestamp, data):
        pass
