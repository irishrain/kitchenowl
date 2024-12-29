import pytest


def test_get_all_households_empty(admin_client):
    response = admin_client.get('/api/household')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_add_household_invalid_data(admin_client):
    # Test missing name
    data = {'member': [1]}
    response = admin_client.post('/api/household', json=data)
    assert response.status_code == 400

    # Test missing members
    data = {'name': 'test'}
    response = admin_client.post('/api/household', json=data)
    assert response.status_code == 400

    # Test empty name
    data = {'name': '', 'member': [1]}
    response = admin_client.post('/api/household', json=data)
    assert response.status_code == 400

def test_get_household_not_found(admin_client):
    response = admin_client.get('/api/household/999999')
    assert response.status_code == 404

def test_delete_household_not_found(admin_client):
    response = admin_client.delete('/api/household/999999')
    assert response.status_code == 404

def test_update_household_unauthorized(user_client, household_id):
    # Try to update a household without being admin
    data = {'name': 'new name'}
    response = user_client.put(f'/api/household/{household_id}', json=data)
    assert response.status_code == 403


def test_add_household_admin(admin_client, household_name):
    response = admin_client.get('/api/user',)
    assert response.status_code == 200
    data = response.get_json()
    admin_user_id = data['id']
    data = {
        'name': household_name,
        'member': [admin_user_id]
    }
    response = admin_client.post('/api/household', json=data)
    assert response.status_code == 200


def test_add_household_user(user_client, household_name):
    response = user_client.get('/api/user',)
    assert response.status_code == 200
    data = response.get_json()
    user_id = data['id']
    data = {
        'name': household_name,
        'member': [user_id]
    }
    response = user_client.post('/api/household', json=data)
    assert response.status_code == 200


def test_get_all_households(user_client_with_household, household_name):
    response = user_client_with_household.get('/api/household',)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == household_name
