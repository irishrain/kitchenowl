from flask import request


class InvalidUsage(Exception):
    def __init__(self, message="Invalid usage", status_code=400):
        super(InvalidUsage, self).__init__(message)
        self.message = message
        self.status_code = status_code


class UnauthorizedRequest(Exception):
    def __init__(self, message=""):
        message = message or "Authorization required. IP {}".format(request.remote_addr)
        super(UnauthorizedRequest, self).__init__(message)
        self.message = message


class ForbiddenRequest(Exception):
    def __init__(self, message="Request forbidden"):
        super(ForbiddenRequest, self).__init__(message)
        self.message = message


class NotFoundRequest(Exception):
    def __init__(self, message="Requested resource not found"):
        super(NotFoundRequest, self).__init__(message)
        self.message = message
