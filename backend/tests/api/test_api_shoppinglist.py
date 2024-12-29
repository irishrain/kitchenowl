import pytest
from app.errors import InvalidUsage


def test_get_shopping_lists_show_all(user_client_with_household, household_id):
    # First create another household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    # Create second household
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Get all shopping lists with show_all=true
    response = user_client_with_household.get(
        f'/api/household/{household_id}/shoppinglist?show_all=true')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2  # Should show lists from both households
    household_ids = {list['household_id'] for list in data}
    assert household_ids == {household_id, second_household_id}


def test_get_shopping_lists(user_client_with_household, household_id):
    response = user_client_with_household.get(
        f'/api/household/{household_id}/shoppinglist',)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert "household_id" in data[0]
    assert data[0]["household_id"] == household_id
    assert "id" in data[0]
    assert "name" in data[0]


def test_add_item_by_name(user_client_with_household, shoppinglist_id, item_name):
    data = {"name": item_name}
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name', json=data)
    assert response.status_code == 200


def test_get_items(user_client_with_household, shoppinglist_id_with_item, item_name):
    response = user_client_with_household.get(
        f'/api/shoppinglist/{shoppinglist_id_with_item}/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert "name" in data[0]
    assert data[0]["name"] == item_name


def test_remove_item(user_client_with_household, shoppinglist_id_with_item, item_id):
    data = {"item_id": item_id}
    response = user_client_with_household.delete(
        f'/api/shoppinglist/{shoppinglist_id_with_item}/item', json=data)
    assert response.status_code == 200
    response = user_client_with_household.get(
        f'/api/shoppinglist/{shoppinglist_id_with_item}/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0


def test_recent_items_household_boundaries(user_client_with_household, household_id, shoppinglist_id):
    # Create second household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Get the second household's default shopping list
    response = user_client_with_household.get(
        f'/api/household/{second_household_id}/shoppinglist')
    assert response.status_code == 200
    second_shoppinglist_id = response.get_json()[0]['id']
    
    # Add and remove an item in first household's list
    data = {"name": "first_household_item"}
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name', json=data)
    assert response.status_code == 200
    first_item_id = response.get_json()['id']
    
    # Remove the item so it appears in recent items
    data = {"item_id": first_item_id}
    response = user_client_with_household.delete(
        f'/api/shoppinglist/{shoppinglist_id}/item', json=data)
    assert response.status_code == 200
    
    # Add and remove an item in second household's list
    data = {"name": "second_household_item"}
    response = user_client_with_household.post(
        f'/api/shoppinglist/{second_shoppinglist_id}/add-item-by-name', json=data)
    assert response.status_code == 200
    second_item_id = response.get_json()['id']
    
    # Remove the item so it appears in recent items
    data = {"item_id": second_item_id}
    response = user_client_with_household.delete(
        f'/api/shoppinglist/{second_shoppinglist_id}/item', json=data)
    assert response.status_code == 200
    
    # Check recent items for first household's list
    response = user_client_with_household.get(
        f'/api/household/{household_id}/shoppinglist')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    recent_items = data[0]['recentItems']
    # Should only see items from first household
    assert len(recent_items) == 1
    assert recent_items[0]['name'] == 'first_household_item'
    
    # Check recent items for second household's list
    response = user_client_with_household.get(
        f'/api/household/{second_household_id}/shoppinglist')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    recent_items = data[0]['recentItems']
    # Should only see items from second household
    assert len(recent_items) == 1
    assert recent_items[0]['name'] == 'second_household_item'


def test_invalid_shoppinglist_operations(user_client_with_household, shoppinglist_id):
    # Test invalid shopping list ID
    response = user_client_with_household.get('/api/shoppinglist/999999/items')
    assert response.status_code == 404

    # Test adding item with invalid JSON
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name',
        data='invalid json',
        content_type='application/json'
    )
    assert response.status_code == 400

    # Test adding item with missing required fields
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name',
        json={}
    )
    assert response.status_code == 400

    # Test removing item with invalid item ID
    response = user_client_with_household.delete(
        f'/api/shoppinglist/{shoppinglist_id}/item',
        json={"item_id": 999999}
    )
    assert response.status_code == 404

def test_shopping_list_item_validation(user_client_with_household, shoppinglist_id):
    # Test empty item name
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name',
        json={'name': ''}
    )
    assert response.status_code == 400

    # Test very long item name (assuming there's a reasonable limit)
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name',
        json={'name': 'a' * 1000}  # Very long name
    )
    assert response.status_code == 400

    # Test special characters in item name
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name',
        json={'name': '<script>alert("xss")</script>'}
    )
    assert response.status_code == 400

def test_cross_household_operations(user_client_with_household, household_id, shoppinglist_id):
    # Create second household with its own item
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    # Create second household
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create an item in second household
    data = {"name": "second_household_item"}
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/item', json=data)
    assert response.status_code == 200
    second_item_id = response.get_json()['id']
    
    # Try to add item from second household to first household's shopping list
    data = {"item_id": second_item_id}
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/item/{second_item_id}', json=data)
    assert response.status_code == 400  # Should fail with InvalidUsage
    
    # Create recipe in second household with its items
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'yields': 4,
        'items': [{'name': 'second_household_item', 'description': '1 piece'}],
        'tags': ['main']
    }
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    recipe = response.get_json()
    
    # Try to add recipe items from second household to first household's shopping list
    data = {
        'items': [{'id': second_item_id, 'description': '1 piece'}]
    }
    response = user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/recipeitems',
        json=data
    )
    assert response.status_code == 400  # Should fail with InvalidUsage
