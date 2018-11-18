from flask import jsonify, make_response
import pickle
import logging

from settings import SERVER_LOG, LOGGING_LEVEL, HEATING_SETTINGS_FILE, TOLERANCE

logging.basicConfig(filename=SERVER_LOG, level=LOGGING_LEVEL, format="%(asctime)s:%(levelname)s:%(message)s")


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


def pickle_it(it, filename):
    with open(filename + '.pickle', 'wb') as file:
        pickle.dump(it,  file, protocol=pickle.HIGHEST_PROTOCOL)
    return


def load_heating_settings_from_file(setting_file=HEATING_SETTINGS_FILE):
    try:
        with open(setting_file, 'rb') as handle:
            settings = pickle.load(handle)
    except FileNotFoundError or IOError:
        logging.error("error while loading timer settings from: %s" % setting_file)
        settings = load_default_heating_settings()
    logging.info("heating settings loaded from %s" % setting_file)
    return settings


def load_default_heating_settings():
    logging.info("fallback to default settings")
    try:
        from timer_settings import DEFAULT_TIMER_SETTINGS
        return DEFAULT_TIMER_SETTINGS
    except ImportError:
        logging.error("couldn't import timer_settings module, can't load default timer settings")
    return {}


def save_heating_settings(setting, setting_file=HEATING_SETTINGS_FILE):
    try:
        with open(setting_file, 'wb') as file:
            pickle.dump(setting, file, protocol=pickle.HIGHEST_PROTOCOL)
    except FileNotFoundError or IOError:
        logging.error("error while saving timer settings to: %s" % setting_file)
        return False
    logging.info("heating settings saved to %s" % setting_file)
    return True
