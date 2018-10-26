New version is based on MQTT protocol using OrangePI PC and arduino boards.
OrangePI is the server, responsible for:
 - collecting data from its temperature sensor, and MQTT enabled (dumb) remote arduino sensors
 - aggregating and recording data (temperature, humidity, heating) to AWS Dynamo DB
 - Storing and managing thermostat settings and timer functionality
 - Switching a relay to turn on/off the heating
 


# OLD VERSION ONLY BASED ON ARDUINO:
## Intelligent thermostat

Software to control arduino getting data from temperature and humidity sensors, 
to serv as an intelligent thermostat and control heating system accordingly through relays.
 
 The program is able to print temperature information to:
   - LCD screen      OK   
   - Serial port     OK
   - HTTP server     OK
   - IOT server      (To be tested) 
  The device can be controlled through IOT server (to be implemented) 
 
  
## Possible improvements :
 - weather forecast using openweather API
 - holiday function (using forecast + historycal info to calculate heat up time)
 - add wireless capability
 - sync time with NTP server 
   
## ISSUES: 
 - running out of usable memory, programming function might be implemented over app, or web 
