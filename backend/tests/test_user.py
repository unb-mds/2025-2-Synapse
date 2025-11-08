import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from app.models.user import User
from app.models.exceptions import UserValidationError, InvalidPasswordError


@pytest.fixture
def valid_user_data():
    """Fixture que fornece dados válidos para criar uma instância de User."""
    return {
        "full_name": "  Test User Name  ",
        "email": "TEST.USER@EXAMPLE.COM",
        "password": "ValidPassword123",
        "birthdate": date(2000, 1, 1),
        "id": 1,
    }


def test_user_creation_with_plain_password(valid_user_data):
    """Testa a criação de um usuário com senha em texto plano."""
    user = User(**valid_user_data)

    assert user.id == 1
    assert user.full_name == "Test User Name"  # Deve ser normalizado
    assert user.email == "test.user@example.com"  # Deve ser normalizado
    assert user.birthdate == date(2000, 1, 1)
    assert hasattr(user, "_password_hash")
    assert user.verify_password("ValidPassword123") is True
    assert user.verify_password("wrongpassword") is False


def test_user_creation_with_hashed_password():
    """Testa a criação de um usuário com uma senha já hasheada."""
    hashed_password = "some_pre_hashed_password"
    user = User(
        full_name="Hashed User",
        email="hashed@example.com",
        password=hashed_password,
        is_hashed=True,
    )

    assert user._password_hash == hashed_password


@pytest.mark.parametrize("invalid_name", [None, "", "  ", "ab", 123])
def test_full_name_validation_raises_error(valid_user_data, invalid_name):
    """Testa se nomes inválidos levantam UserValidationError."""
    with pytest.raises(UserValidationError, match="Nome completo deve ter pelo menos 3 caracteres"):
        valid_user_data["full_name"] = invalid_name
        User(**valid_user_data)


@pytest.mark.parametrize("invalid_email", [None, "", "invalid-email", "test@", "@example.com", 123])
def test_email_validation_raises_error(valid_user_data, invalid_email):
    """Testa se e-mails inválidos levantam UserValidationError."""
    with pytest.raises(UserValidationError, match="Formato de email inválido|Email não pode ser vazio"):
        valid_user_data["email"] = invalid_email
        User(**valid_user_data)


def test_reading_password_raises_attribute_error(valid_user_data):
    """Testa se a tentativa de ler o atributo 'password' levanta um erro."""
    user = User(**valid_user_data)
    with pytest.raises(AttributeError, match="'password' não é um atributo legível"):
        _ = user.password


@pytest.mark.parametrize("invalid_password, error_msg", [
    (None, "A senha não pode ser vazia"),
    ("", "A senha não pode ser vazia"),
    ("short", "A senha deve ter no mínimo 8 caracteres"),
    ("nouppercase1", "A senha deve conter ao menos uma letra maiúscula"),
    ("NOLOWERCASE1", "A senha deve conter ao menos uma letra minúscula"),
    ("NoNumber", "A senha deve conter ao menos um número"),
])
def test_password_setter_validation_raises_error(valid_user_data, invalid_password, error_msg):
    """Testa se senhas inválidas levantam InvalidPasswordError."""
    with pytest.raises(InvalidPasswordError, match=error_msg):
        valid_user_data["password"] = invalid_password
        User(**valid_user_data)


def test_verify_password_with_no_hash(valid_user_data):
    """Testa a verificação de senha em um objeto sem hash de senha."""
    user = User(**valid_user_data)
    user._password_hash = None  # Simula um estado inválido
    assert user.verify_password("any_password") is False


@pytest.fixture
def mock_user_entity():
    """Fixture que cria um mock de UserEntity."""
    entity = MagicMock()
    entity.id = 10
    entity.full_name = "Entity User"
    entity.email = "entity@example.com"
    entity.birthdate = date(1995, 5, 5)
    # Simula um hash gerado pelo werkzeug
    entity.password_hash = "pbkdf2:sha256:600000$salt$hash"
    return entity


def test_from_entity_with_full_data(mock_user_entity):
    """Testa a criação de um User a partir de uma entidade com todos os dados."""
    # Mockar a função de verificação para isolar o teste
    with patch('app.models.user.check_password_hash', return_value=True) as mock_check:
        user = User.from_entity(mock_user_entity)

        assert user.id == mock_user_entity.id
        assert user.full_name == mock_user_entity.full_name
        assert user.email == mock_user_entity.email
        assert user.birthdate == mock_user_entity.birthdate
        assert user._password_hash == mock_user_entity.password_hash

        # Verifica se a senha pode ser validada
        assert user.verify_password("any_password") is True
        mock_check.assert_called_once_with(mock_user_entity.password_hash, "any_password")


def test_from_entity_with_none_entity():
    """Testa se from_entity retorna None para uma entidade nula."""
    assert User.from_entity(None) is None


def test_to_orm(valid_user_data):
    """
    Testa a conversão de uma instância de User para uma UserEntity.
    Verifica se os atributos corretos são passados para o construtor da entidade.
    """
    # Usamos patch para substituir a UserEntity no módulo 'app.models.user'
    with patch('app.models.user.UserEntity') as MockUserEntity:
        user = User(**valid_user_data)
        orm_entity = user.to_orm()

        # Verifica se o construtor da entidade mockada foi chamado com os argumentos corretos
        MockUserEntity.assert_called_once_with(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            birthdate=user.birthdate,
            password_hash=user._password_hash,
            newsletter=user.newsletter,
        )

        # O retorno de to_orm() deve ser a instância criada pelo construtor mockado
        assert orm_entity == MockUserEntity.return_value


def test_repr_method(valid_user_data):
    """Testa a representação em string do objeto User."""
    user = User(**valid_user_data)
    expected_repr = f"<User(id={user.id}, email='{user.email}')>"
    assert repr(user) == expected_repr
