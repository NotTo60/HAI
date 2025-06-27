class BaseConnector:
    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def exec_command(self, command):
        raise NotImplementedError

    def is_alive(self):
        """Check if the connection is still alive and functional."""
        raise NotImplementedError
