import json
import pytest
from app.models.custom_topic import CustomTopic
from app.models.topic import Topic
from app.entities.user_preferred_custom_topics import UserPreferredCustomTopicEntity

valid_user_data = {
    "full_name": "Test User",
    "email": "test.user@example.com",
    "password": "StrongPassword123",
    "newsletter": False
}

def get_auth_client(client, user_data):
    client.post('/users/register', data=json.dumps(user_data), content_type='application/json')
 
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    client.post(
        '/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
 
    csrf_cookie = client.get_cookie('csrf_access_token')
    csrf_token = ""
    if csrf_cookie:
        csrf_token = csrf_cookie.value
 
    headers = {'X-CSRF-TOKEN': csrf_token}
    return client, headers

def test_add_topic_to_user_successfully(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)

    request_data = {
        "name": "tecnologia"
    }
    response = auth_client.post(
        '/topics/custom',
        data=json.dumps(request_data),
        content_type='application/json',
        headers=headers
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert "Tópico adicionado com sucesso." in data['message']
    assert data['data']['topic']['name'] == "Tecnologia"

def test_add_existing_topic_to_user_successfully(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)

    topic = CustomTopic(name="política").to_orm()
    db.session.add(topic)
    db.session.commit()

    request_data = {
        "name": "política"
    }
    response = auth_client.post(
        '/topics/custom',
        data=json.dumps(request_data),
        content_type='application/json',
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert "Tópico adicionado com sucesso." in data['message']
    assert data['data']['topic']['name'] == "Política"

def test_add_topic_to_user_without_name_fails(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)

    response = auth_client.post(
        '/topics/custom',
        data=json.dumps({}),
        content_type='application/json',
        headers=headers
    )

    assert response.status_code == 400
    error_data = response.get_json()
    assert "Campo 'name' é obrigatório." in error_data['message']

def test_get_user_topics_successfully(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)
    
    auth_client.post('/topics/custom', data=json.dumps({"name": "saúde"}), content_type='application/json', headers=headers)
    auth_client.post('/topics/custom', data=json.dumps({"name": "economia"}), content_type='application/json', headers=headers)

    response = auth_client.get('/topics/custom', headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['data']['topics']) == 2
    topic_names = [t['name'] for t in data['data']['topics']]
    assert "Saúde" in topic_names
    assert "Economia" in topic_names

def test_get_user_topics_no_topics(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)
    response = auth_client.get('/topics/custom', headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['data']['topics']) == 0

def test_remove_topic_from_user_successfully(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)

    topic = CustomTopic(name="arte").to_orm()
    db.session.add(topic)
    db.session.flush()
    
    user_topic = UserPreferredCustomTopicEntity(user_id=1, topic_id=topic.id)
    db.session.add(user_topic)
    db.session.commit()
    
    response = auth_client.delete(f'/topics/custom/{topic.id}', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Tópico removido das preferências com sucesso." in data['message']

    association = db.session.query(UserPreferredCustomTopicEntity).filter_by(user_id=1, topic_id=topic.id).first()
    assert association is None

def test_remove_nonexistent_topic_from_user_fails(client, db):
    auth_client, headers = get_auth_client(client, valid_user_data)
    
    response = auth_client.delete(f'/topics/custom/999', headers=headers)
    assert response.status_code == 404
    error_data = response.get_json()
    assert "Tópico não encontrado." in error_data['message']

def test_topic_routes_without_token_fails(client):
    response = client.get('/topics/custom') 
    assert response.status_code == 401

    response = client.post(
        '/topics/custom',
        data=json.dumps({"name": "test"}),
        content_type='application/json'
    )
    assert response.status_code == 401

    response = client.delete('/topics/custom/1')
    assert response.status_code == 401
