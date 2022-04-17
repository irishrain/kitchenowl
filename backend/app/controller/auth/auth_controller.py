from app.helpers import validate_args
from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from app.models import User
from app.errors import UnauthorizedRequest
from .schemas import Login

auth = Blueprint('auth', __name__)


@auth.route('', methods=['POST'])
@validate_args(Login)
def login(args):
    username = args['username'].lower()
    user = User.find_by_username(username)
    if not user or not user.check_password(args['password']):
        raise UnauthorizedRequest(message='Unauthorized')
    ret = {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username)
    }
    return jsonify(ret)


@auth.route('/fresh-login', methods=['POST'])
@validate_args(Login)
def fresh_login(args):
    username = args['username'].lower()
    user = User.find_by_username(username.lower())
    if not user or not user.check_password(args['password']):
        raise UnauthorizedRequest(message='Unauthorized')
    ret = {'access_token': create_access_token(identity=username, fresh=True)}
    return jsonify(ret), 200


@auth.route('/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    user = User.find_by_username(get_jwt_identity())
    if not user:
        raise UnauthorizedRequest(message='Unauthorized')
    ret = {
        'access_token': create_access_token(identity=user.username)
    }
    return jsonify(ret)
