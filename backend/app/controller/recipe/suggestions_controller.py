from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
from app.helpers import authorize_household
from app.models import Recipe

recipe_suggestions = Blueprint("recipe_suggestions", __name__)

@recipe_suggestions.route("/suggestions", methods=["GET"])
@jwt_required()
@authorize_household()
def get_recipe_suggestions(household_id):
    """Get recipe suggestions for a household"""
    Recipe.compute_suggestion_ranking(household_id)
    suggestions = Recipe.find_suggestions(household_id)
    
    if not suggestions:
        return jsonify({
            'suggestions': [],
            'message': 'No recipe suggestions available. This could be because:\n' +
                      '1. No recipes have been added yet\n' +
                      '2. All recipes are currently planned\n' +
                      '3. No recipes have received suggestion scores'
        })
        
    return jsonify({
        'suggestions': [recipe.obj_to_full_dict() for recipe in suggestions],
        'message': f'Found {len(suggestions)} recipe suggestions'
    })