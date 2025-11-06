import re
from datetime import date
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.exceptions import UserValidationError, InvalidPasswordError
from app.entities.user_entity import UserEntity


class User:
    def __init__(
        self,
        full_name: str,
        email: str,
        password: str,
        id: Optional[int] = None,
        birthdate: Optional[date] = None,
        is_hashed: bool = False,
        newsletter: bool = False,
    ):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.birthdate = birthdate
        if is_hashed:
            self._password_hash = password
        else:
            self.password = password
        self.newsletter = newsletter

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        if not value or not isinstance(value, str) or len(value.strip()) < 3:
            raise UserValidationError("full_name", "Nome completo deve ter pelo menos 3 caracteres.")
        self._full_name = value.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        if not value or not isinstance(value, str):
            raise UserValidationError("email", "Email não pode ser vazio.")
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise UserValidationError("email", "Formato de email inválido.")
        self._email = value.lower()

    @property
    def password(self):
        raise AttributeError("'password' não é um atributo legível.")

    @password.setter
    def password(self, plain_password: str):
        if not plain_password or not isinstance(plain_password, str):
            raise InvalidPasswordError("A senha não pode ser vazia.")
        if len(plain_password) < 8:
            raise InvalidPasswordError("A senha deve ter no mínimo 8 caracteres.")
        if not re.search(r"[A-Z]", plain_password):
            raise InvalidPasswordError("A senha deve conter ao menos uma letra maiúscula.")
        if not re.search(r"[a-z]", plain_password):
            raise InvalidPasswordError("A senha deve conter ao menos uma letra minúscula.")
        if not re.search(r"\d", plain_password):
            raise InvalidPasswordError("A senha deve conter ao menos um número.")

        self._password_hash = generate_password_hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        if not hasattr(self, '_password_hash') or not self._password_hash or not plain_password:
            return False
        return check_password_hash(self._password_hash, plain_password)

    @classmethod
    def from_entity(cls, entity: UserEntity) -> 'User':
        if not entity:
            return None
        return cls(
            id=entity.id,
            full_name=entity.full_name,
            email=entity.email,
            birthdate=entity.birthdate,
            password=entity.password_hash, 
            is_hashed=True,
            newsletter=entity.newsletter
        )

    def to_orm(self) -> UserEntity:
        return UserEntity(
            id=self.id,
            full_name=self.full_name,
            email=self.email,
            birthdate=self.birthdate,
            password_hash=self._password_hash,
            newsletter=self.newsletter
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
