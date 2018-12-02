JSON_ERROR = {"error": "Bad request", "code": "400", "message": "Field missing, or bad format!"}
DAY_ERROR = {"error": "Wrong format", "code": "400", "message": "Wrong day name, try: Monday, Tuesday etc..."}
TIME_ERROR = {"error": "Wrong format", "code": "400",
              "message": "Error wrong hour or minute(hours 0-23, minutes: 0-59)"}
PARAM_ERROR = {"error": "Wrong parameters", "code": "400",
              "message": "Error wrong parameters: if hour is present, day has to be present, if minute is present, hour and day has to be present"}
