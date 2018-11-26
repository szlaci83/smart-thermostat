MAIN_SETTINGS = {'HEAT_THRESHOLD': 0.8,
                 'TEMP_TOLERANCE': 1,
                 'HUM_TOLERANCE': 10,
                 'MAIN_SENSOR': 'mock_location1'}

if __name__ == '__main__':
    from utils import pickle_it
    pickle_it(MAIN_SETTINGS, "main_settings")
    print("pickled: " + str(MAIN_SETTINGS))
