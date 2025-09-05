from flask_jwt_extended import create_access_token

def test_jwt_login_valid_credentials(client, user):
    """
    Test JWT login with valid credentials.
    """
    response = client.post('/token/', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access' in response_json


def test_jwt_login_invalid_credentials(client):
    """
    Test JWT login with invalid credentials.
    """
    response = client.post('/token/', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    assert response.get_json() == {'detail': 'Invalid username or password'}


def test_user_list_requires_authentication_without_token(client, user):
    """
    Test that the user list endpoint requires authentication.
    """
    # Without token
    response = client.get('/list/')
    assert response.status_code == 401
    assert response.get_json() == {'msg': 'Missing Authorization Header'}

def test_user_list_requires_authentication_with_token(client, user):
    # With token
    response = client.post('/token/', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    access_token = response.get_json().get('access')
    response = client.get('/list/', headers={'Authorization': f'Bearer {access_token}'})
    print(response.get_json())
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['username'] == 'testuser'
