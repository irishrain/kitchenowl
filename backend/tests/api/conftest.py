import pytest
from app import app, db


@pytest.fixture
def client():
    app_context = app.app_context()
    app_context.push()
    app.config['TESTING'] = True
    db.create_all()
    client = app.test_client()
    yield client
    db.session.rollback()
    db.drop_all()
    app_context.pop()


@pytest.fixture
def username():
    return "testuser"


@pytest.fixture
def name():
    return "testname"


@pytest.fixture
def password():
    return "testpwd"


@pytest.fixture
def admin_username():
    return "testadmin"


@pytest.fixture
def admin_name():
    return "adminname"


@pytest.fixture
def admin_password():
    return "adminpwd"


@pytest.fixture
def household_name():
    return "testhousehold"


@pytest.fixture
def onboarded_client(client, admin_username, admin_name, admin_password):
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    return client


@pytest.fixture
def admin_client(client, admin_username, admin_name, admin_password):
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    data = response.get_json()
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {data["access_token"]}'
    return client


@pytest.fixture
def user_client(admin_client, username, name, password):
    data = {
        'username': username,
        'name': name,
        'password': password
    }
    response = admin_client.post('/api/user/new', json=data)
    data = {
        'username': username,
        'password': password
    }
    response = admin_client.post('/api/auth', json=data)
    data = response.get_json()
    admin_client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {data["access_token"]}'
    return admin_client


@pytest.fixture
def user_client_with_household(user_client, household_name):
    response = user_client.get('/api/user',)
    assert response.status_code == 200
    data = response.get_json()
    user_id = data['id']
    data = {
        'name': household_name,
        'member': [user_id]
    }
    response = user_client.post('/api/household', json=data)
    return user_client
