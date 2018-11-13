from multiprocessing import Queue
from forceheating import ForceHeating


class CurrentState:
    q = Queue()
    humidity = 0
    temperature = 0
    temperature = 0
    humidities = {}
    temperatures = {}
    weather_data = {}
    TIMER_SETTINGS = {}
    HEATING = False
    FORCE_HEATING = ForceHeating.UNSET

