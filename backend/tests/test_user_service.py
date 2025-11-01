import pytest
from unittest.mock import MagicMock
from datetime import date
from app.services.user_service import UserService
from app.models.user import User
from app.models.exceptions import (
    UserValidationError,
    InvalidPasswordError,
    UserNotFoundError,
    EmailInUseError,
    NewsNotFoundError,
    NewsAlreadyFavoritedError,
    NewsNotFavoritedError,
)
from sqlalchemy.exc import SQLAlchemyError

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(repo=mock_user_repo)

@pytest.fixture
def test_user_data():
    return {
        "full_name": "Test User",
        "email": "test.user@example.com",
        "password": "StrongPassword123",
        "birthdate": "1990-01-01",
    }
    

def test_register_successfully(user_service, mock_user_repo, test_user_data):
    mock_user_repo.find_by_email.return_value = None
    
    created_user_model = User(
        id=1,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        is_hashed=False,
    )
    mock_user_repo.create.return_value = created_user_model
    
    registered_user = user_service.register(test_user_data)
    
    mock_user_repo.find_by_email.assert_called_once_with(test_user_data["email"].lower())
    mock_user_repo.create.assert_called_once()
    
    assert isinstance(registered_user, User)
    assert registered_user.full_name == test_user_data["full_name"]
    assert registered_user.email == test_user_data["email"].lower()
    assert registered_user.id == 1
    
def test_register_duplicate_email_raises_error(user_service, mock_user_repo, test_user_data):
    
    existing_user_model = User(
        id=1,
        full_name="Existing User",
        email=test_user_data["email"],
        password="SomeHashedPassword",
        is_hashed=True,
    )
    
    mock_user_repo.find_by_email.return_value = existing_user_model
    
    with pytest.raises(EmailInUseError) as e:
        user_service.register(test_user_data)
        
    assert "E-mail já cadastrado" in str(e.value)
    mock_user_repo.find_by_email.assert_called_once_with(test_user_data["email"].lower())
    mock_user_repo.create.assert_not_called()
    

def test_register_with_invalid_email_format_int_model(user_service, mock_user_repo, test_user_data):
    invalid_data = test_user_data.copy()
    invalid_data["email"] = "invalid-email-format"
    
    with pytest.raises(ValueError) as e:
        user_service.register(invalid_data)
        
    assert "Erro de validação em 'email': Formato de email inválido." in str(e.value)
    mock_user_repo.find_by_email.assert_not_called()
    mock_user_repo.create.assert_not_called()
    
def test_register_missing_required_field_raises_error(user_service):
    incomplete_data = {"full_name": "Test User", "password": "StrongPassword123"}
    
    with pytest.raises(KeyError) as e:
        user_service.register(incomplete_data)
        
    assert "Campo obrigatório ausente: 'email'" in str(e.value)

def test_register_sqlalchemy_error_raises_exception(user_service, mock_user_repo, test_user_data):
    mock_user_repo.find_by_email.return_value = None
    mock_user_repo.create.side_effect = SQLAlchemyError
    
    with pytest.raises(Exception) as e:
        user_service.register(test_user_data)
    
    assert "Ocorreu um erro ao registrar o usuário no banco de dados." in str(e.value)
    mock_user_repo.create.assert_called_once()
    
def test_login_successfully(user_service, mock_user_repo, test_user_data):
    user_model_in_db = User(
        id=1,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        is_hashed=False,
    )
    mock_user_repo.find_by_email.return_value = user_model_in_db
    
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],

    }
    logged_in_user = user_service.login(login_data)
    
    assert logged_in_user is not None
    assert logged_in_user.email == test_user_data["email"].lower()
    mock_user_repo.find_by_email.assert_called_once_with(test_user_data["email"].lower())


def test_login_wrong_password(user_service, mock_user_repo, test_user_data):
    user_model_in_db = User(
        id=1,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        
    )
    mock_user_repo.find_by_email.return_value = user_model_in_db
    
    login_data = {
        "email": test_user_data["email"],
        "password": "WrongPassword123",
        
    }
    
    logged_in_user = user_service.login(login_data)
    
    assert logged_in_user is None
    mock_user_repo.find_by_email.assert_called_once_with(test_user_data["email"].lower())
    
def test_login_user_not_found(user_service, mock_user_repo, test_user_data):
    mock_user_repo.find_by_email.return_value = None
    
    login_data = {
        "email": "nonexistent.user@example.com",
        "password": "Password123"
        
    }
    
    logged_in_user = user_service.login(login_data)
    
    assert logged_in_user is None
    mock_user_repo.find_by_email.assert_called_once_with("nonexistent.user@example.com")
    

def test_login_missing_fields_raises_error(user_service):
    with pytest.raises(ValueError) as e:
        user_service.login({"email": "test@example.com"})
        
    assert "E-mail e senha são obrigatórios." in str(e.value)

def test_get_profile_successful(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    mock_user_repo.find_by_id.return_value = user_model_in_db
    
    profile = user_service.get_profile(user_id)
    
    assert profile is not None
    assert profile.id == user_id
    mock_user_repo.find_by_id.assert_called_once_with(user_id)

def test_get_profile_user_not_found(user_service, mock_user_repo):
    user_id = 999
    mock_user_repo.find_by_id.return_value = None
    
    profile = user_service.get_profile(user_id)
    
    assert profile is None
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    
def test_update_profile_successful(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    
    updated_data = {
        "full_name": "Updated Name",
        "birthdate": "1995-05-05"
    }
    
    updated_user_model = User(
        id=user_id,
        full_name=updated_data["full_name"],
        email=test_user_data["email"],
        password=user_model_in_db._password_hash,
        birthdate=date(1995, 5, 5),
        is_hashed=True
    )
    
    mock_user_repo.find_by_id.return_value = user_model_in_db
    mock_user_repo.update.return_value = updated_user_model
    mock_user_repo.find_by_email.return_value = None
    
    updated_user = user_service.update_profile(user_id, updated_data)
    
    assert updated_user.full_name == updated_data["full_name"]
    assert str(updated_user.birthdate) == updated_data["birthdate"]
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_called_once()
    mock_user_repo.find_by_email.assert_not_called()

def test_update_profile_user_not_found_raises_error(user_service, mock_user_repo):
    user_id = 999
    mock_user_repo.find_by_id.return_value = None
    
    updated_data = { "full_name": "New Name" }
    
    with pytest.raises(UserNotFoundError) as e:
        user_service.update_profile(user_id, updated_data)
    
    assert "Usuário não encontrado" in str(e.value)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_not_called()

def test_update_profile_email_already_in_use_raises_error(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    
    other_user_model = User(
        id=2,
        full_name="Another User",
        email="another.user@example.com",
        password="AnotherPassword",
        is_hashed=True,
    )
    
    updated_data = {
        "email": "another.user@example.com"
    }
    
    mock_user_repo.find_by_id.return_value = user_model_in_db
    mock_user_repo.find_by_email.return_value = other_user_model
    
    with pytest.raises(EmailInUseError) as e:
        user_service.update_profile(user_id, updated_data)
    
    assert "O novo e-mail já está em uso." in str(e.value)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.find_by_email.assert_called_once_with(updated_data["email"].lower())
    mock_user_repo.update.assert_not_called()

def test_update_profile_invalid_value_raises_error(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    
    invalid_data = {
        "email": "not-an-email"
    }
    
    mock_user_repo.find_by_id.return_value = user_model_in_db
    
    with pytest.raises(ValueError) as e:
        user_service.update_profile(user_id, invalid_data)
        
    assert "Erro de validação em 'email': Formato de email inválido." in str(e.value)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.find_by_email.assert_not_called()
    mock_user_repo.update.assert_not_called()

def test_change_password_successful(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    mock_user_repo.find_by_id.return_value = user_model_in_db
    
    new_password = "NewStrongPassword123"
    mock_user_repo.update.return_value = None
    
    user_service.change_password(user_id, {"new_password": new_password})
    
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_called_once()
    assert user_model_in_db.verify_password(new_password)

def test_change_password_user_not_found_raises_error(user_service, mock_user_repo):
    user_id = 999
    mock_user_repo.find_by_id.return_value = None
    
    with pytest.raises(UserNotFoundError) as e:
        user_service.change_password(user_id, {"new_password": "NewPassword123"})
        
    assert "Usuário não encontrado" in str(e.value)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_not_called()

def test_change_password_invalid_password_raises_error(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    mock_user_repo.find_by_id.return_value = user_model_in_db
    
    invalid_password = "weak"
    with pytest.raises(ValueError) as e:
        user_service.change_password(user_id, {"new_password": invalid_password})
        
    assert "A senha deve ter no mínimo 8 caracteres." in str(e.value)
    mock_user_repo.find_by_id.assert_called_once_with(user_id)
    mock_user_repo.update.assert_not_called()

def test_change_password_missing_password_raises_error(user_service, mock_user_repo, test_user_data):
    user_id = 1
    user_model_in_db = User(
        id=user_id,
        full_name=test_user_data["full_name"],
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    mock_user_repo.find_by_id.return_value = user_model_in_db
    
    with pytest.raises(ValueError) as e:
        user_service.change_password(user_id, {})
    
    assert "Senha é obrigatório." in str(e.value)
    mock_user_repo.find_by_id.assert_not_called()
    mock_user_repo.update.assert_not_called()
    
def test_favorite_news_successfully(user_service, mock_user_repo):
    """Testa se a chamada para favoritar uma notícia é bem-sucedida."""
    user_id, news_id = 1, 100
    mock_user_repo.add_favorite_news.return_value = None
    
    user_service.favorite_news(user_id, news_id)
    
    mock_user_repo.add_favorite_news.assert_called_once_with(user_id, news_id)

@pytest.mark.parametrize("expected_exception", [
    UserNotFoundError,
    NewsNotFoundError,
    NewsAlreadyFavoritedError
])
def test_favorite_news_raises_known_exceptions(user_service, mock_user_repo, expected_exception):
    """Testa se exceções conhecidas do repositório são propagadas corretamente."""
    user_id, news_id = 1, 100
    mock_user_repo.add_favorite_news.side_effect = expected_exception("Error")
    
    with pytest.raises(expected_exception):
        user_service.favorite_news(user_id, news_id)
        
    mock_user_repo.add_favorite_news.assert_called_once_with(user_id, news_id)

def test_favorite_news_raises_generic_exception_on_unexpected_error(user_service, mock_user_repo):
    """Testa se uma exceção genérica é levantada para erros inesperados."""
    user_id, news_id = 1, 100
    mock_user_repo.add_favorite_news.side_effect = SQLAlchemyError("DB Connection Error")
    
    with pytest.raises(Exception, match="Ocorreu um erro interno ao favoritar a notícia."):
        user_service.favorite_news(user_id, news_id)
        
    mock_user_repo.add_favorite_news.assert_called_once_with(user_id, news_id)

def test_unfavorite_news_successfully(user_service, mock_user_repo):
    """Testa se a chamada para desfavoritar uma notícia é bem-sucedida."""
    user_id, news_id = 1, 100
    mock_user_repo.remove_favorite_news.return_value = None
    
    user_service.unfavorite_news(user_id, news_id)
    
    mock_user_repo.remove_favorite_news.assert_called_once_with(user_id, news_id)

@pytest.mark.parametrize("expected_exception", [
    UserNotFoundError,
    NewsNotFavoritedError
])
def test_unfavorite_news_raises_known_exceptions(user_service, mock_user_repo, expected_exception):
    """Testa se exceções conhecidas do repositório são propagadas ao desfavoritar."""
    user_id, news_id = 1, 100
    mock_user_repo.remove_favorite_news.side_effect = expected_exception("Error")
    
    with pytest.raises(expected_exception):
        user_service.unfavorite_news(user_id, news_id)
        
    mock_user_repo.remove_favorite_news.assert_called_once_with(user_id, news_id)

def test_unfavorite_news_raises_generic_exception_on_unexpected_error(user_service, mock_user_repo):
    """Testa se uma exceção genérica é levantada para erros inesperados ao desfavoritar."""
    user_id, news_id = 1, 100
    mock_user_repo.remove_favorite_news.side_effect = Exception("Unexpected Error")
    
    with pytest.raises(Exception, match="Ocorreu um erro interno ao desfavoritar a notícia."):
        user_service.unfavorite_news(user_id, news_id)
        
    mock_user_repo.remove_favorite_news.assert_called_once_with(user_id, news_id)
    
    