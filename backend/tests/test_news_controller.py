import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.controllers.news_controller import NewsController
from app.models.exceptions import NewsNotFoundError, NewsSourceAlreadyAttachedError

@pytest.fixture
def mock_user_service():
    with patch('app.controllers.news_controller.UserService') as mock:
        yield mock.return_value

@pytest.fixture
def mock_news_service():
    with patch('app.controllers.news_controller.NewsService') as mock:
        yield mock.return_value

@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield app

@pytest.fixture
def controller(mock_user_service, mock_news_service, app_context):
    c = NewsController()
    c.user_service = mock_user_service
    c.news_service = mock_news_service
    return c

def test_favorite_news_success(controller, mock_user_service):
    user_id, news_id = 1, 10
    response, status_code = controller.favorite_news(user_id, news_id)
    assert status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Notícia favoritada."
    mock_user_service.favorite_news.assert_called_once_with(user_id, news_id)

def test_favorite_news_already_favorited(controller, mock_user_service):
    user_id, news_id = 1, 10
    mock_user_service.favorite_news.side_effect = NewsSourceAlreadyAttachedError("Já favoritada.")
    response, status_code = controller.favorite_news(user_id, news_id)
    assert status_code == 409
    assert response.json["success"] is False
    assert response.json["message"] == "Já favoritada."

def test_favorite_news_generic_error(controller, mock_user_service):
    user_id, news_id = 1, 10
    mock_user_service.favorite_news.side_effect = Exception("DB Error")
    response, status_code = controller.favorite_news(user_id, news_id)
    assert status_code == 500
    assert response.json["success"] is False
    assert response.json["message"] == "Erro ao favoritar notícia."

def test_unfavorite_news_success(controller, mock_user_service):
    user_id, news_id = 1, 10
    response, status_code = controller.unfavorite_news(user_id, news_id)
    assert status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Notícia removida dos favoritos."
    mock_user_service.unfavorite_news.assert_called_once_with(user_id, news_id)

def test_unfavorite_news_generic_error(controller, mock_user_service):
    user_id, news_id = 1, 10
    mock_user_service.unfavorite_news.side_effect = Exception("DB Error")
    response, status_code = controller.unfavorite_news(user_id, news_id)
    assert status_code == 500
    assert response.json["success"] is False
    assert response.json["message"] == "Erro ao remover favorito."

def test_get_news_success(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context('/?page=2&per_page=5'):
        mock_news_service.get_news_for_user.return_value = {"news": [], "total": 0, "pages": 0}
        response, status_code = controller.get_news(user_id)
        assert status_code == 200
        assert response.json["success"] is True
        mock_news_service.get_news_for_user.assert_called_once_with(user_id, 2, 5)

def test_get_news_generic_error(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context():
        mock_news_service.get_news_for_user.side_effect = Exception("DB Error")
        response, status_code = controller.get_news(user_id)
        assert status_code == 500
        assert response.json["success"] is False
        assert response.json["message"] == "Erro ao obter notícias."

def test_get_by_id_success(controller, mock_news_service):
    user_id, news_id = 1, 10
    mock_news_service.get_news_by_id.return_value = {"id": news_id, "title": "Test"}
    response, status_code = controller.get_by_id(user_id, news_id)
    assert status_code == 200
    assert response.json["success"] is True
    assert response.json["data"]["id"] == news_id
    mock_news_service.get_news_by_id.assert_called_once_with(user_id, news_id)

def test_get_by_id_not_found(controller, mock_news_service):
    user_id, news_id = 1, 999
    mock_news_service.get_news_by_id.side_effect = NewsNotFoundError("Notícia não encontrada")
    response, status_code = controller.get_by_id(user_id, news_id)
    assert status_code == 404
    assert response.json["success"] is False
    assert response.json["message"] == "Notícia não encontrada."
    
def test_get_by_topic_success(controller, mock_news_service, app_context):
    user_id, topic_id = 1, 5
    with app_context.test_request_context('/?page=1'):
        mock_news_service.get_news_by_topic.return_value = {"news": [], "total": 0, "pages": 0}
        response, status_code = controller.get_by_topic(user_id, topic_id)
        assert status_code == 200
        assert response.json["success"] is True
        mock_news_service.get_news_by_topic.assert_called_once_with(topic_id, 1, 10, user_id)

def test_get_by_topic_generic_error(controller, mock_news_service, app_context):
    user_id, topic_id = 1, 5
    with app_context.test_request_context():
        mock_news_service.get_news_by_topic.side_effect = Exception("DB Error")
        response, status_code = controller.get_by_topic(user_id, topic_id)
        assert status_code == 500
        assert response.json["success"] is False
        assert response.json["message"] == "Erro interno do servidor."

def test_get_for_you_news_success(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context('/?page=1&per_page=20'):
        mock_news_service.get_for_you_news.return_value = {"news": [], "total": 0, "pages": 0}
        response, status_code = controller.get_for_you_news(user_id)
        assert status_code == 200
        assert response.json["success"] is True
        mock_news_service.get_for_you_news.assert_called_once_with(user_id, 1, 20)

def test_get_for_you_news_generic_error(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context():
        mock_news_service.get_for_you_news.side_effect = Exception("DB Error")
        response, status_code = controller.get_for_you_news(user_id)
        assert status_code == 500
        assert response.json["success"] is False
        assert response.json["message"] == "Erro ao obter feed personalizado."
        
def test_get_favorite_news_success(controller, mock_news_service):
    user_id = 1
    mock_news_service.get_favorite_news.return_value = [{"id": 10, "title": "Favorite"}]
    response, status_code = controller.get_favorite_news(user_id)
    assert status_code == 200
    assert response.json["success"] is True
    assert len(response.json["data"]) == 1
    mock_news_service.get_favorite_news.assert_called_once_with(user_id)

def test_get_favorite_news_not_found(controller, mock_news_service):
    user_id = 1
    mock_news_service.get_favorite_news.side_effect = NewsNotFoundError("Nenhuma notícia favorita encontrada.")
    response, status_code = controller.get_favorite_news(user_id)
    assert status_code == 404
    assert response.json["success"] is False
    assert response.json["message"] == "Notícias favoritas não encontrada."

def test_save_history_news_success(controller, mock_news_service):
    user_id, news_id = 1, 10
    response, status_code = controller.save_history_news(user_id, news_id)
    assert status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "Noticia acessada."
    mock_news_service.save_history.assert_called_once_with(user_id, news_id)

def test_save_history_news_generic_error(controller, mock_news_service):
    user_id, news_id = 1, 10
    mock_news_service.save_history.side_effect = Exception("DB Error")
    response, status_code = controller.save_history_news(user_id, news_id)
    assert status_code == 500
    assert response.json["success"] is False
    assert response.json["message"] == "Erro salvar acesso a noticia."

def test_get_history_news_success(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context('/?page=2&per_page=5'):
        mock_news_service.get_history_news.return_value = {"history": [], "total": 0, "pages": 0}
        response, status_code = controller.get_history_news(user_id)
        assert status_code == 200
        assert response.json["success"] is True
        assert response.json["message"] == "Histórico de notícias obtido com sucesso."
        mock_news_service.get_history_news.assert_called_once_with(user_id, 2, 5)

def test_get_history_news_default_pagination(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context('/'):
        mock_news_service.get_history_news.return_value = {"history": [], "total": 0, "pages": 0}
        response, status_code = controller.get_history_news(user_id)
        assert status_code == 200
        assert response.json["success"] is True
        mock_news_service.get_history_news.assert_called_once_with(user_id, 1, 10)

def test_get_history_news_invalid_pagination_resets_to_defaults(controller, mock_news_service, app_context):
    user_id = 1
    # Testa com página negativa e per_page excessivo
    with app_context.test_request_context('/?page=-1&per_page=200'):
        mock_news_service.get_history_news.return_value = {"history": [], "total": 0, "pages": 0}
        response, status_code = controller.get_history_news(user_id)
        assert status_code == 200
        assert response.json["success"] is True
        # Verifica se a página foi corrigida para 1 e per_page para 10 (o default)
        mock_news_service.get_history_news.assert_called_once_with(user_id, 1, 10)

def test_get_history_news_generic_error(controller, mock_news_service, app_context):
    user_id = 1
    with app_context.test_request_context():
        mock_news_service.get_history_news.side_effect = Exception("DB Error")
        response, status_code = controller.get_history_news(user_id)
        assert status_code == 500
        assert response.json["success"] is False
        assert response.json["message"] == "Erro ao buscar histórico de notícias."