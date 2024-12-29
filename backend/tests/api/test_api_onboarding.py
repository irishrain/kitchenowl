import pytest


def test_onboarding_status_true(client):
    response = client.get('/api/onboarding',)
    assert response.status_code == 200
    data = response.get_json()
    assert "onboarding" in data
    assert data["onboarding"] == True


def test_onboarding_status_false(onboarded_client):
    response = onboarded_client.get('/api/onboarding',)
    assert response.status_code == 200
    data = response.get_json()
    assert "onboarding" in data
    assert data["onboarding"] == False


def test_onboarding(client, admin_username, admin_name, admin_password):
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_onboarding_invalid_data(client):
    # Test missing username
    data = {
        'name': 'Test Name',
        'password': 'password123'
    }
    response = client.post('/api/onboarding', json=data)
    assert response.status_code == 400

    # Test missing name
    data = {
        'username': 'testuser',
        'password': 'password123'
    }
    response = client.post('/api/onboarding', json=data)
    assert response.status_code == 400

    # Test missing password
    data = {
        'username': 'testuser',
        'name': 'Test Name'
    }
    response = client.post('/api/onboarding', json=data)
    assert response.status_code == 400

    # Test empty username
    data = {
        'username': '',
        'name': 'Test Name',
        'password': 'password123'
    }
    response = client.post('/api/onboarding', json=data)
    assert response.status_code == 400

    # Test empty password
    data = {
        'username': 'testuser',
        'name': 'Test Name',
        'password': ''
    }
    response = client.post('/api/onboarding', json=data)
    assert response.status_code == 400

def test_onboarding_duplicate_username(client, admin_username, admin_name, admin_password):
    # First onboarding
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    assert response.status_code == 200

    # Try to onboard with same username
    onboard_data = {
        'username': admin_username,
        'name': 'Different Name',
        'password': 'different_password'
    }
    response = client.post('/api/onboarding', json=onboard_data)
    assert response.status_code == 400

def test_onboarding_malformed_json(client):
    response = client.post('/api/onboarding', data='not a json')
    assert response.status_code == 400
