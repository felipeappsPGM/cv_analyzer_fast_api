# app/schemas/enums.py
from enum import Enum

class UserTypeEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"