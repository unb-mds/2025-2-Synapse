
import json
import re

valid_user_data = {
    "full_name": "Test User",
    "email": "test.user@example.com",
    "password": "StrongPassword123",
    "newsletter": False
}

def get_auth_client(client, user_data):
    client.post('/users/register', data=json.dumps(user_data), content_type='application/json')
    login_response = client.post(
        '/users/login',
        data=json.dumps({"email": user_data["email"], "password": user_data["password"]}),
        content_type = 'application/json'
    )
    csrf_cookie = client.get_cookie('csrf_access_token')
    csrf_token = ""
    if csrf_cookie:
        csrf_token = csrf_cookie.value

    headers = {'X-CSRF-TOKEN': csrf_token}
    return client, headers

    



def test_register_user_successfully(client):
    response = client.post(
        '/users/register',
        data=json.dumps(valid_user_data),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert "Usuário registrado com sucesso" in data['message']

def test_register_with_duplicate_email(client):
    client.post('/users/register', data=json.dumps(valid_user_data), content_type='application/json')
    
    response = client.post(
        '/users/register',
        data=json.dumps(valid_user_data),
        content_type='application/json'
    )
    assert response.status_code == 409
    error_data = response.get_json()
    assert "E-mail já cadastrado" in error_data['error']

def test_register_with_missing_required_field(client):
    incomplete_data = valid_user_data.copy()
    del incomplete_data['email']

    response = client.post(
        '/users/register',
        data=json.dumps(incomplete_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    error_data = response.get_json()
    assert "Campo obrigatório ausente" in error_data['error']
    assert "'email'" in error_data['error']

def test_register_with_invalid_email_format(client):
    invalid_data = valid_user_data.copy()
    invalid_data['email'] = "email-invalido" 
    
    response = client.post(
        '/users/register',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    error_data = response.get_json()
    assert "Erro de validação em 'email': Formato de email inválido." in error_data['error']

def test_register_with_weak_password(client):
    invalid_data = valid_user_data.copy()
    invalid_data['password'] = "123" 
    
    response = client.post(
        '/users/register',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    error_data = response.get_json()
    assert "A senha deve ter no mínimo 8 caracteres" in error_data['error']

def test_login_successfully(client):
    client.post('/users/register', data=json.dumps(valid_user_data), content_type='application/json')
    
    login_data = {
        "email": valid_user_data["email"],
        "password": valid_user_data["password"]
    }
    
    response = client.post(
        '/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Login bem-sucedido" in data['message']
    assert data['data']['email'] == valid_user_data['email']
    assert 'access_token_cookie' in response.headers.get('Set-Cookie')

def test_login_with_wrong_password(client):

    client.post('/users/register', data=json.dumps(valid_user_data), content_type='application/json')
    
    login_data = {
        "email": valid_user_data["email"],
        "password": "wrongpassword"
    }
    
    response = client.post(
        '/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    error_data = response.get_json()
    assert "Credenciais inválidas" in error_data['error']
    
    
def test_get_profile_successfully(client):
    auth_client, headers = get_auth_client(client, valid_user_data)
    response = auth_client.get('/users/profile', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['email'] == valid_user_data['email']

def test_get_profile_without_token_fails(client):
    response = client.get('/users/profile')
    assert response.status_code == 401

def test_update_profile_sucessfully(client):
   auth_client, headers = get_auth_client(client, valid_user_data)
   update_data = {
       "full_name": "Updated Name",
       "birthdate": "1995-05-05"
   
   }
   response = auth_client.put(
       '/users/profile/update',
       data=json.dumps(update_data),
       content_type='application/json',
       headers=headers

   )
   
   assert response.status_code == 200
   data = response.get_json()
   assert data ['success'] is True
   assert data['data']['full_name'] == "Updated Name"
   assert data['data']['birthdate'] == "1995-05-05"
   
def test_update_profile_with_existing_email_fails(client):
    user1_data = {
        "full_name": "User One",
        "email": "user1@example.com",
        "password": "Password123",
        "newsletter": False
    }
    client.post('/users/register', data=json.dumps(user1_data), content_type='application/json')
    
    user2_data = {
        "full_name": "User Two",
        "email": "user2@example.com",
        "password": "Password123",
        "newsletter": False
    }
    auth_client, headers = get_auth_client(client, user2_data)
    
    update_data = {"email": user1_data["email"]}
    response = auth_client.put(
        '/users/profile/update',
        data=json.dumps(update_data),
        content_type='application/json',
        headers=headers
    )
    assert response.status_code == 409
    error_data = response.get_json()
    assert "O novo e-mail já está em uso." in error_data['error']
    
def test_update_password_successfully(client):
    auth_client, headers = get_auth_client(client, valid_user_data)
    new_password_data = {
        "new_password": "NewStrongPassword123"
    }
    response = auth_client.put(
        '/users/profile/change_password',
        data=json.dumps(new_password_data),
        content_type='application/json',
        headers=headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Senha alterada com sucesso." in data['message']

def test_update_password_with_weak_password_fails(client):
    auth_client, headers = get_auth_client(client, valid_user_data)
    new_password_data = {
        "new_password": "weak"
    }
    response = auth_client.put(
        '/users/profile/change_password',
        data=json.dumps(new_password_data),
        content_type='application/json',
        headers=headers
    )
    assert response.status_code == 400
    error_data = response.get_json()
    assert "A senha deve ter no mínimo 8 caracteres." in error_data['error']

def test_logout_successfully(client):
    auth_client, headers = get_auth_client(client, valid_user_data)
    response = auth_client.post('/users/logout', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert "Logout bem-sucedido." in data['message']
    set_cookie_header = response.headers.get('Set-Cookie')
    assert 'access_token_cookie=;' in set_cookie_header
    assert 'Expires=Thu, 01 Jan 1970 00:00:00 GMT' in set_cookie_header