# app/core/validators.py
import re
from pydantic import validator

def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Senha deve ter pelo menos 8 caracteres")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("Senha deve conter pelo menos uma letra minúscula")
    if not re.search(r"\d", password):
        raise ValueError("Senha deve conter pelo menos um número")
    return password