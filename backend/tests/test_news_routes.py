import json
import pytest
from datetime import datetime, timezone
from app.extensions import db
from app.models.user import User
from app.entities.user_entity import UserEntity
from app.entities.topic_entity import TopicEntity
from app.entities.news_entity import NewsEntity
from app.entities.news_source_entity import NewsSourceEntity
from app.entities.user_read_history_entity import UserReadHistoryEntity

def get_auth_client(client, user_data):
    
    client.post('/users/register', data=json.dumps(user_data), content_type='application/json')
    login_response = client.post('/users/login', data=json.dumps({
        'email': user_data['email'],
        'password': user_data['password']
    }), content_type='application/json')
    
    csrf_cookie = client.get_cookie('csrf_access_token')
    csrf_token_value = ""
    if csrf_cookie:
        csrf_token_value = csrf_cookie.value
    headers = {'X-CSRF-TOKEN': csrf_token_value}
    return client, headers


@pytest.fixture
def news_setup(db):
    """
    Cria um setup completo com usuário, tópico, fonte e notícia.
    """
    # 1. Criar Usuário
    user_data = {
        "full_name": "News User",
        "email": "news.user@example.com",
        "password": "StrongPassword123"
    }
    user_model = User(
        full_name=user_data["full_name"],
        email=user_data["email"],
        password=user_data["password"]
    )
    user_entity = user_model.to_orm()
    db.session.add(user_entity)
    
    # 2. Criar Tópico
    topic = TopicEntity(name="Geral")
    db.session.add(topic)
    
    # 3. Criar Fonte
    source = NewsSourceEntity(name="Jornal Teste", url="http://jornal.teste.com")
    db.session.add(source)
    
    db.session.commit() # Commit para obter os IDs
    
    # 4. Criar Notícia
    news = NewsEntity(
        title="Notícia de Teste",
        description="Descrição da notícia.",
        url="http://jornal.teste.com/noticia1",
        content="Conteúdo completo da notícia.",
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        topic_id=topic.id
    )
    db.session.add(news)
    
    db.session.commit()
    
    return {
        "user_data": user_data,
        "user_id": user_entity.id,
        "topic_id": topic.id,
        "source_id": source.id,
        "news_id": news.id
    }
    
def test_get_news_by_id_unauthenticated(client, news_setup):
    news_id = news_setup["news_id"]
    response = client.get(f'/news/{news_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['id'] == news_id
    assert data['data']['title'] == "Notícia de Teste"
    assert data['data']['is_favorited'] is False
    
def test_get_news_by_id_authenticated(client, news_setup):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    news_id = news_setup["news_id"]
    
    response = auth_client.get(f'/news/{news_id}', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['id'] == news_id
    assert data['data']['is_favorited'] is False
    
def test_get_news_by_id_not_found(client):
    response = client.get('/news/9999')  # ID inexistente
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert "Notícia não encontrada" in data['message']
    
def test_save_news_history(client, news_setup):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    news_id = news_setup["news_id"]
    
    response = auth_client.post(f'/news/{news_id}/history', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Noticia acessada" in data['message']
    
    # Verificar se o histórico foi salvo no banco de dados
    history_entry = UserReadHistoryEntity.query.filter_by(
        user_id=news_setup["user_id"],
        news_id=news_setup["news_id"]
    ).first()
    assert history_entry is not None
    
def test_get_news_history(client, news_setup, db):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    
    # Adicionar entrada de histórico manualmente
    history_entry = UserReadHistoryEntity(
        user_id=news_setup["user_id"],
        news_id=news_setup["news_id"],
    )
    db.session.add(history_entry)
    db.session.commit()
    
    response = auth_client.get('/news/history', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['pagination']['total'] == 1
    assert len(data['data']['news']) == 1
    assert data['data']['news'][0]['id'] == news_setup["news_id"]
    
    
def test_favorite_and_unfavorite_news(client, news_setup):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    news_id = news_setup["news_id"]

    response_fav = auth_client.post(f'/news/{news_id}/favorite', headers=headers)
    assert response_fav.status_code == 200
    data_fav = response_fav.get_json()
    assert "Notícia favoritada" in data_fav['message']
    
    response_get = auth_client.get('/news/saved', headers=headers)
    data_get = response_get.get_json()
    assert data_get['data']['pagination']['total'] == 1
    assert data_get['data']['news'][0]['id'] == news_id
    
    response_unfav = auth_client.put(f'/news/{news_id}/favorite', headers=headers)
    assert response_unfav.status_code == 200
    data_unfav = response_unfav.get_json()
    assert "Notícia removida dos favoritos" in data_unfav['message']
    
    response_get_empty = auth_client.get('/news/saved', headers=headers)
    data_get_empty = response_get_empty.get_json()
    assert data_get_empty['data']['pagination']['total'] == 0
    assert len(data_get_empty['data']['news']) == 0

def test_favorite_already_favorited_news_fails(client, news_setup):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    news_id = news_setup["news_id"]

    auth_client.post(f'/news/{news_id}/favorite', headers=headers)
    
    response_fav_again = auth_client.post(f'/news/{news_id}/favorite', headers=headers)
    
    assert response_fav_again.status_code == 500 # Erro interno, pois o controller não trata NewsAlreadyFavoritedError
    data_fav_again = response_fav_again.get_json()
    assert "Erro ao favoritar notícia" in data_fav_again['message']

def test_get_news_by_topic(client, news_setup):
    topic_id = news_setup["topic_id"]
    response = client.get(f'/news/topic/{topic_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['pagination']['total'] == 1
    assert data['data']['news'][0]['id'] == news_setup["news_id"]
    assert data['data']['news'][0]['topic_name'] == "Geral"

def test_get_for_you_news(client, news_setup):
    auth_client, headers = get_auth_client(client, news_setup["user_data"])
    
    response = auth_client.get('/news/for-you', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Feed personalizado obtido com sucesso" in data['message']
    assert len(data['data']['news']) > 0
    assert data['data']['news'][0]['id'] == news_setup["news_id"]