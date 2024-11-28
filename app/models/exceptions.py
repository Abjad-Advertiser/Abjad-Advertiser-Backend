class ModelError(Exception):
    def __init__(self, reason: str, status: int):
        self.reason = reason
        self.status = status
        super().__init__(f"Error {status}: {reason}")
