import pytest
from app.models import Recipe, RecipeItems, RecipeTags

def test_recipe_creation_with_required_fields(user_client_with_household, household_id):
    """Test creating a recipe with all required fields"""
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['main', 'vegetarian'],
        'items': []
    }
    
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    recipe = response.get_json()
    assert recipe['name'] == 'Test Recipe'
    assert recipe['cook_time'] == 20
    assert recipe['prep_time'] == 10
    assert len(recipe['tags']) == 2

def test_recipe_creation_missing_required_fields(user_client_with_household, household_id):
    """Test recipe creation with missing required fields"""
    test_cases = [
        # Missing cook_time
        {
            'name': 'Test Recipe',
            'description': 'Test Description',
            'yields': 4,
            'time': 30,
            'prep_time': 10,
            'tags': ['main']
        },
        # Missing prep_time
        {
            'name': 'Test Recipe',
            'description': 'Test Description',
            'yields': 4,
            'time': 30,
            'cook_time': 20,
            'tags': ['main']
        },
        # Missing tags
        {
            'name': 'Test Recipe',
            'description': 'Test Description',
            'yields': 4,
            'time': 30,
            'cook_time': 20,
            'prep_time': 10
        }
    ]

    for test_case in test_cases:
        response = user_client_with_household.post(
            f'/api/household/{household_id}/recipe',
            json=test_case
        )
        assert response.status_code == 400

def test_recipe_with_invalid_tags(user_client_with_household, household_id):
    """Test recipe creation with invalid tags"""
    # Test empty tag name - should fail
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': [''],  # Empty tag name
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test whitespace tag - should fail
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': [' '],  # Whitespace tag
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test empty tags list - should pass
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': [],  # Empty tags list
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

    # Test missing tags field - should pass
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

def test_recipe_with_cross_household_items(user_client_with_household, household_id, second_household):
    """Test recipe creation with items from different household"""
    # Create an item in second household
    item_data = {'name': 'Cross Household Item'}
    response = user_client_with_household.post(
        f'/api/household/{second_household}/item',
        json=item_data
    )
    assert response.status_code == 200
    cross_item = response.get_json()

    # Try to use the item in a recipe for first household
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['main'],
        'items': [{'id': cross_item['id'], 'description': '1 piece'}]
    }
    
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

def test_recipe_update_with_invalid_fields(user_client_with_household, recipe_with_items):
    """Test recipe update with invalid field values"""
    recipe_id = recipe_with_items
    
    # Test negative cook_time - should fail
    recipe_data = {
        'name': 'Updated Recipe',
        'description': 'Updated Description',
        'yields': 4,
        'time': 30,
        'cook_time': -20,
        'prep_time': 10
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test negative prep_time - should fail
    recipe_data = {
        'name': 'Updated Recipe',
        'description': 'Updated Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': -10
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test zero yields - should pass
    recipe_data = {
        'name': 'Updated Recipe',
        'description': 'Updated Description',
        'yields': 0,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=recipe_data
    )
    assert response.status_code == 200

    # Test negative yields - should fail
    recipe_data = {
        'name': 'Updated Recipe',
        'description': 'Updated Description',
        'yields': -1,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=recipe_data
    )
    assert response.status_code == 400

def test_recipe_suggestions(user_client_with_household, household_id):
    """Test recipe suggestions functionality"""
    # Create multiple recipes
    recipes = []
    for i in range(3):
        recipe_data = {
            'name': f'Test Recipe {i}',
            'description': f'Test Description {i}',
            'yields': 4,
            'time': 30,
            'cook_time': 20,
            'prep_time': 10,
            'tags': ['main'],
            'items': []
        }
        response = user_client_with_household.post(
            f'/api/household/{household_id}/recipe',
            json=recipe_data
        )
        assert response.status_code == 200
        recipes.append(response.get_json())

    # Test suggestion ranking
    Recipe.compute_suggestion_ranking(household_id)
    
    # Get suggestions
    response = user_client_with_household.get(f'/api/household/{household_id}/recipe/suggestions')
    assert response.status_code == 200
    result = response.get_json()
    
    # Verify response structure
    assert 'suggestions' in result
    assert 'message' in result
    assert isinstance(result['suggestions'], list)
    assert len(result['suggestions']) > 0
    
    # Verify each suggestion has required fields
    for suggestion in result['suggestions']:
        assert 'id' in suggestion
        assert 'name' in suggestion
        assert 'description' in suggestion
        assert 'time' in suggestion
        assert 'cook_time' in suggestion
        assert 'prep_time' in suggestion
        assert 'yields' in suggestion
        assert 'tags' in suggestion

def test_recipe_search_special_chars(user_client_with_household, household_id):
    """Test recipe search with special characters"""
    # Create a recipe with special characters
    recipe_data = {
        'name': 'Test*Recipe_With?Special%Chars',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['main'],
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

    # Test searching with wildcards
    test_searches = [
        'Test*Recipe',
        'Recipe_With',
        'Special%'
    ]
    for search in test_searches:
        response = user_client_with_household.get(
            f'/api/household/{household_id}/recipe/search?query={search}'
        )
        assert response.status_code == 200
        results = response.get_json()
        assert len(results) > 0

def test_recipe_filter_by_tags(user_client_with_household, household_id):
    """Test filtering recipes by tags"""
    # Create recipes with different tags
    recipe_data1 = {
        'name': 'Vegetarian Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['vegetarian', 'main'],
        'items': []
    }
    recipe_data2 = {
        'name': 'Meat Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['meat', 'main'],
        'items': []
    }

    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data1
    )
    assert response.status_code == 200

    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data2
    )
    assert response.status_code == 200

    # Test filtering by tag
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe/filter',
        json={'filter': ['vegetarian']}
    )
    assert response.status_code == 200
    results = response.get_json()
    assert len(results) == 1
    assert results[0]['name'] == 'Vegetarian Recipe'

def test_recipe_export_import(user_client_with_household, household_id):
    """Test recipe export and import functionality"""
    # Create a recipe
    recipe_data = {
        'name': 'Export Test Recipe',
        'description': 'Test Description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'tags': ['main'],
        'items': [{'name': 'test_item', 'description': '1 piece'}]
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    recipe_id = response.get_json()['id']

    # Export recipe
    response = user_client_with_household.get(f'/api/recipe/{recipe_id}/export')
    assert response.status_code == 200
    exported_data = response.get_json()
    assert exported_data['name'] == 'Export Test Recipe'
    assert len(exported_data['items']) == 1
    assert len(exported_data['tags']) == 1