class BaseConnector:
    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def exec_command(self, command):
        raise NotImplementedError
