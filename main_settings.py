MAIN_SETTINGS = {'THRESHOLD': 0.8,
                 'MAIN_SENSOR': 'mock_location1'}

if __name__ == '__main__':
    from utils import pickle_it

    pickle_it(MAIN_SETTINGS, "main_settings")
