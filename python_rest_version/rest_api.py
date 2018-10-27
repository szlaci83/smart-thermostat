#!/usr/bin/env python
from flask import Flask, jsonify, request, Response, make_response,  current_app
from flask_cors import CORS
import orangepi_controller as controller

app = Flask(__name__)
CORS(app)

@app.route("/status", methods=['GET'])
def get_status():
    response = jsonify("OK"), 200
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['content-type'] = "application/json"
    return response

@app.route("/switch", methods=['POST'])
def switch():
    if not request.json or not 'state' in request.json:
        response = jsonify({"error" : "Bad request", "code": "400", "message" : "No state or bad format."}, 400)
        make_response(response)
        return response
    state = request.json['state']
   # if state == "on":
       # controller.turn_led_on()
	
   # else:
      #  controller.turn_led_off()

    response = jsonify(state, 200)
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['content-type'] = "application/json"
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0')
