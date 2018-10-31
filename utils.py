from flask import jsonify, make_response


def add_headers(response, http_code, token=None):
    '''
    Wraps a Http response and a given http code into CORS and JSON headers
    :param response: The response to wrap
    :param http_code: The http code to wrap
    :param token: JWT token
    :return: the wrapped HTTP response with headers
    '''
    response = jsonify(response), http_code
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['content-type'] = "application/json"
    if token is not None:
        response.headers['Authorization'] = token
    return response


def validate_req(req, fields):
    '''
    Validates a http request against a list of required fields
    :param req: the http request
    :param fields: the required fields
    :return: False if the request does not contain all the required fields, True otherwise
    '''
    for field in fields:
        if not req.json or field not in req.json:
            return False
    return True