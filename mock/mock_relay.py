# Mocking Relay on/ off


def off(led=True):
    if led:
        turn_led_off()
    print("Heating OFF")


def on(led=True):
    if led:
        turn_led_on()
    print("Heating ON")


def turn_led_on():
    print("LED ON")


def turn_led_off():
    print("LED OFF")