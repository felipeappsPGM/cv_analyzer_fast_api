# =============================================
# app/core/exceptions.py
# =============================================
class AppException(Exception):
    """Base exception"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UserNotFoundError(AppException):
    pass

class UserAlreadyExistsError(AppException):
    pass