from functools import wraps
from enum import Enum
from flask_jwt_extended import current_user
from app.errors import UnauthorizedRequest, ForbiddenRequest
from app.models import HouseholdMember


class RequiredRights(Enum):
    MEMBER = 1
    ADMIN = 2
    ADMIN_OR_SELF = 3


def authorize_household(required: RequiredRights = RequiredRights.MEMBER):
    def wrapper(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if "household_id" not in kwargs:
                raise Exception("Wrong usage of authorize_household")
            if required == RequiredRights.ADMIN_OR_SELF and "user_id" not in kwargs:
                raise Exception("Wrong usage of authorize_household")
            if not current_user:
                raise UnauthorizedRequest()

            # First check if user is a server admin
            if current_user.admin:
                return func(*args, **kwargs)

            # Get the user's membership in this household
            member = HouseholdMember.find_by_ids(
                kwargs["household_id"], current_user.id
            )

            # Check if user is a member of this household
            if not member:
                # Special case: if this is a self-operation and user has ADMIN_OR_SELF rights
                if (
                    required == RequiredRights.ADMIN_OR_SELF
                    and current_user.id == kwargs["user_id"]
                ):
                    return func(*args, **kwargs)
                raise ForbiddenRequest()

            # Now we know the user is a member, check specific rights
            if required == RequiredRights.MEMBER:
                return func(*args, **kwargs)

            # For admin operations, check if user is admin/owner
            if required == RequiredRights.ADMIN and (member.admin or member.owner):
                return func(*args, **kwargs)

            # For ADMIN_OR_SELF operations
            if required == RequiredRights.ADMIN_OR_SELF:
                if member.admin or member.owner:
                    return func(*args, **kwargs)
                if current_user.id == kwargs["user_id"]:
                    return func(*args, **kwargs)

            raise ForbiddenRequest()

        return decorator

    return wrapper
