/*Thermostat:
 *  -white -> 3v3
 *  -orange -> digital 2
 *  -yellow -> N/A
 *  -blue -> ground
 *   
 * 
 * Software to control arduino getting data from temperature and humidity sensors, 
 * to serv as an intelligent thermostat and control heating system accordingly through relays.
 * 
 * The program is able to print temperature information to:
 *  - LCD screen      OK   
 *  - Serial port     OK
 *  - HTTP server     OK
 *  - IOT server      (To be tested) 
 * The device can be controlled through IOT server (to be implemented) 
 *
 * (As new functionality is Internet connection, there might not be room for button shield afterall.
 *  Therefore button functions and menu system might be left out, and be fully app controlled)  
 *  
 * Possible improvements :
 * - weather forecast using openweather API
 * - holiday function (using forecast + historycal info to calculate heat up time)
 * - add wireless capability
 * - sync time with NTP server 
 *  
 * ISSUES: 
 * - running out of usable memory, programming function might be implemented over app, or web 
 *  
 * Laszlo Szoboszlai 
 * 10/11/2015
*/

#include "DHT.h"
#include "math.h"
#include "MenuSystem.h"
#include <LiquidCrystal.h>
#include <SPI.h>
#include <Ethernet.h>
#include <ThingSpeak.h> 
//TODO :  include WIFI header and implement WIFI option

// initialize the LCD library with the numbers of the interface pins
LiquidCrystal lcd(8, 9, 4, 5, 6, 7);
DHT dht;

//SETTING UP THE SERVER:
//mac address of the ethernet shield
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
//chosen ip address:
//IPAddress ip(192, 168, 0, 177);
IPAddress ip(10, 1, 27, 147);
// Initialize the Ethernet server 
// with the IP address and port we want to use
// (port 80 is default for HTTP):
//EthernetServer server(80);



// ThingSpeak Settings
  byte IOTserver[]  = { 184, 106, 153, 149 };
  char thingSpeakAddress[] = "api.thingspeak.com";
  String writeAPIKey = "THE KEY";
  unsigned long ChannelNumber = 80982;
 // #define WRITE_DELAY_FOR_THINGSPEAK 15000      // Time interval in milliseconds to update ThingSpeak 
   EthernetClient client;
 
  

//creating a byte array to represent a smiley 
byte smiley[8] = {
  0b00000,
  0b00000,
  0b01010,
  0b00000,
  0b00000,
  0b10001,
  0b01110,
  0b00000
};
byte fire[8] = {
  0b00100,
  0b01100,
  0b01110,
  0b11110,
  0b11110,
  0b11111,
  0b11111,
  0b01110
};
byte wifi[8] = {
  0b00000,
  0b01110,
  0b10001,
  0b00100,
  0b01010,
  0b00000,
  0b01110,
  0b01110
};
byte wired[8] = {
  0b01110,
  0b01110,
  0b00100,
  0b01110,
  0b01010,
  0b11011,
  0b11011,
  0b00000
};




//constant values to store some characteristics:
  const float MAX_HUM = 50; //maximum of ideal humidity
  const float MIN_HUM = 30; //minimum of ideal humidity
  const int DAYS = 7; //number of days the programmer can handle 
  const int PERIODS = 12;  //periods per day
  const float IDEAL_TEMP = 20.0; // ideal temperature to set the thermostat to
  const float INIT_TERESHOLD = 1.0; //the value above the desired temperature it stops the heating
  const int BACKLIT_PIN = 10;  //Set backlitpint to 10

// used variables:
  float humidity;
  float temperature;
  float dewPoint;
  double heatIndex;
  float desiredTemp; //desired temperature set on thermostat
  float tereshold;
  unsigned long time=0; 
     
  boolean heating = false; //flag representing heating status
  boolean is_wifi = false; //flag representing wifi connection
  boolean is_eth = false; // flag represanting ethernet connection
   
 // float PROG[DAYS][PERIODS];  // array storing the desired temperatures 
  
  int button = 0;    
  int lastButton = 0; 

//SETUP  
void setup()
{
  //start ThingSpeak client
    Ethernet.begin(mac);
    ThingSpeak.begin(client);
    
  Serial.begin(9600);
  //create new character (1=smiley, 2=fire, 3=wired, 4=wifi)
  //TODO Write them out accordingly 
  lcd.createChar(1, smiley);
  lcd.createChar(2, fire);
  lcd.createChar(3, wired);
  lcd.createChar(4, wifi);
  
//set data pins  
 // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);
 //set buttons up on analogpin 0
   pinMode(A0, INPUT);
   
 //set backlit to digital pin 10 and set it on
  pinMode(BACKLIT_PIN, OUTPUT);
  digitalWrite(BACKLIT_PIN,HIGH);

 //Start the server:
 // Ethernet.begin(mac, ip);
//  server.begin();
  Serial.print("server is at ");
  Serial.println(Ethernet.localIP());
  is_eth = true;
  
 //set the sensor to data pin 2 
  dht.setup(2); 
  
 // initial message on the screeen:
 /* BLOCKED OUT TO SPEED UP TESTING
  lcd.setCursor(0,0);
  lcd.print("   Intelligent  ");
  lcd.setCursor(0,1);
  lcd.print("   Thermostat ");
  lcd.write((byte) 1);
  delay(3000);
  lcd.clear();

  lcd.setCursor(0,0);
  lcd.print("    Version     ");
  lcd.setCursor(0,1);
  lcd.print("    1.0 beta    ");
  delay(3000);
  lcd.clear();
 */ 
  //initialise values
  temperature = 0.0;
  humidity = 0.0; 
  dewPoint = 0.0;
  heatIndex = 0.0;
  desiredTemp = IDEAL_TEMP;
  tereshold = INIT_TERESHOLD;
  
/*   
  //populate the matrix storing temp settings with the ideal temp value
  for(int i = 0; i < DAYS; i++){
     for(int j = 0; j < PERIODS; j ++){
        PROG[i][i] = IDEAL_TEMP;
     }
   }*/
}

//FUNCTIONS TO CALCULATE VALUES AND PRINT OUT DATA ETC...


 
//simpler calculation that gives an approximation of dew point temperature if you know the observed temperature and relative humidity
//the following formula was proposed in a 2005 article by Mark G. Lawrence in the Bulletin of the American Meteorological Society:
//Td = T - ((100 - RH)/5.)     T in celsius, RH in percent (fairly accurate if RH>50%

float getDewPointSimple(float T, float RH){
  return (T - ((100 - RH) / 5.0));  
}


// dew point complex calculation according to : Martin Wanielista, Robert Kersten and Ron Eaglin. 1997. Hydrology Water Quantity and Quality Control. 
// John Wiley & Sons. 2nd ed.    T in celsius, RH in percent 
 
float getDewPointComplex(float T, float RH){
   return (pow((RH / 100), ( 1 / 8 )) * (112 + 0.9 * T) + 0.1 * T - 112);
}

//Uses the appropriate function to calculate dew point.
float getDewPoint(float T, float RH){
   float dPoint = 0.0;
     //only use the simple method if humidity>=50 %, so its accurate enough
        if (humidity < 50){
              dPoint = getDewPointComplex(temperature, humidity);    
            }
        else {
              dPoint = getDewPointSimple(temperature, humidity);
            }
   return dPoint;
}

//Calculation of Heat index:
//Source: http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml

//The computation of the heat index is a refinement of a result obtained by multiple regression 
//analysis carried out by Lans P. Rothfusz and described in a 1990 National Weather Service (NWS) 
//Technical Attachment (SR 90-23). 
//T = ambient dry bulb temperature (°F)
//RH = relative humidity (integer percentage)

double HIRothfusz(double T, double RH){
  double heatInd = 0.0;
  //setting constats used in formula
  const double C1 = -42.379;
  const double C2 = 2.04901523;
  const double C3 = 10.14333127;
  const double C4 = -0.22475541;
  const double C5 = -0.00683783;
  const double C6 = -0.05481717;
  const double C7 = 0.00122874;
  const double C8 = 0.00085282;
  const double C9 = -0.00000199;
/*
 //alternative setting:
 
  const double C1 = 0.36445176;
  const double C2 = 0.988622465;
  const double C3 = 4.777114035;
  const double C4 = -0.114037667;
  const double C5 = -0.000850208;
  const double C6 = -0.020716198;
  const double C7 = 0.000687678;
  const double C8 = 0.000274954;
  const double C9 = 0.0;
*/
  //calculate heatindex 
  heatInd = C1 + 
             (C2 * T) + 
             (C3 * RH) + 
             (C4 * T * RH) + 
             (C5 * T * T)  + 
             (C6 * RH *RH) + 
             (C7 * T * T * RH) +  
             (C8 *T * RH * RH) + 
             (C9 *T *T * RH * RH);
             
  return dht.toCelsius(heatInd); //returns the heatindex converted back to celsius  
}

//The Rothfusz regression is not appropriate when conditions of temperature and humidity 
//warrant a heat index value below about 80 degrees F. In those cases, a simpler formula 
//is applied to calculate values consistent with Steadman's results:
//HI = 0.5 * {T + 61.0 + [(T-68.0)*1.2] + (RH*0.094)}

double HISteadman(double T, double RH){
  double heatInd = 0.0;
  //constants used in formula:
    const double C1 = 0.5;
    const double C2 = 61.0;
    const double C3 = 68.0;
    const double C4 = 1.2;
    const double C5 = 0.094;

     return (C1 * (T + C2 + ((T-C3)*C4) + (RH * C5)));
}

//Uses Steadman equation if temperature is greater than 80F (26C)
//otherwise uses Rothfusz equation to calculate heat index. 
double getHeatIndex(double TC, double RH){
  double heatInd = 0.0;
  double  T = dht.toFahrenheit(TC); // the formula needs the temperature in fahrenheit 
  //choose which formula is appropriate:
  if (T < 80) {
    heatInd = HISteadman(T, RH);
  }
  else {
    heatInd = HIRothfusz(T, RH);
  }
  return heatInd;
}

//Functions to print data in various ways:

//write data to serial port (PC com port, USB in our case)
void printDataToSerial(float Temp,float Hum, float Hindex, float Dpoint){
     Serial.println("Temp:\tHum:\tHeatInd:\tDewp.:");
     Serial.print(Temp);
     Serial.print("\t");
     Serial.print(Hum);
     Serial.print("\t");
     Serial.print(Hindex);
     Serial.print("\t\t");
     Serial.print(Dpoint);
     Serial.println();
}

//send data to server:
void sendDataToServer(float Temp,float Hum, float Hindex, float Dpoint, boolean CHeat){
//  EthernetClient client = server.available();
  if (client) {
    Serial.println("new client");
    // an http request ends with a blank line
    boolean currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        Serial.write(c);
        // if you've gotten to the end of the line (received a newline
        // character) and the line is blank, the http request has ended,
        // so you can send a reply
        if (c == '\n' && currentLineIsBlank) {
          // send a standard http response header
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/html");
          client.println("Connection: close");  // the connection will be closed after completion of the response
          client.println("Refresh: 5");  // refresh the page automatically every 5 sec
          client.println();
          client.println("<!DOCTYPE HTML>");
          client.println("<html>");
          //send the line of data to server
          client.print("{Temperature:");
          client.print(Temp); 
          client.print(",Humidity:"); 
          client.print(Hum);
          client.print(",Heat Index:");
          client.print(Hindex);
          client.print(",Dew Point:");
          client.print(Dpoint);
          client.print(",Heating:");
          client.print(CHeat);
          client.println("}");
          
            client.println("<br />");
      
          client.println("</html>");
          break;
        }
        if (c == '\n') {
          // no more character in the line
          currentLineIsBlank = true;
        }
        else if (c != '\r') {
          // there are still a character on the current line
          currentLineIsBlank = false;
        }
      }
    }
    // give the web browser time to receive the data
    delay(1);
    // close the connection:
    client.stop();
    Serial.println("client disconnected");
} 
}

//write data to LCD 
//print the first static line on lcd
//TODO print connection info     
void printFirstline(float Temp,float Hum, boolean CHeat){  
    String firstLine ="T:" + (String)Temp + "C " + (String)Hum + "%";
     if (CHeat) { 
        lcd.write((byte) 2);  // print the "fire" simbol 
        }
     lcd.print(firstLine);
}

//Handles the first static + second scrolling line problem
void printMainScreenOnLCD(float Temp,float Hum, float Hindex, float Dpoint, boolean CHeat,String Inf, int Delay){
    lcd.clear(); 
    printFirstline(Temp,Hum,CHeat);
    String secondLine ="** Central Heating set to: " + (String)IDEAL_TEMP +" C **** Heat Index :" + (String)Hindex + " C **** Dew Point: " + (String)Dpoint + " C****" + Inf; 
   for (int i = 0; i < secondLine.length() -15; i++){
      lcd.setCursor(0, 1);
      lcd.print(secondLine.substring(i,i + 16));
      if (buttonPress(0) < 900){break;} ;    
      delay(Delay);
      lcd.setCursor(0, 1);
      //delete second line
      lcd.print("                ");
   }
   delay(Delay * 2);
 }
 

//IOT
void sendDataToIOT(float Temp,float Hum, float Hindex, float Dpoint, boolean CHeat){
    // update example http://api.thingspeak.com/update?key=C606GJW98AWMN9P9&field1=10&field2=20
 String url = "http://api.thingspeak.com/update?key=" + writeAPIKey + "&field1=" + Temp;

  //int i = url.length;
 char urlc[url.length()+1] ;

 url.toCharArray(urlc,url.length()+1);
  if (client.connect(urlc , 80)) {
    Serial.println("connected");
    // Make a HTTP request:
    //client.print("GET /search?q=arduino HTTP/1.1");
    //client.println("Host: www.google.com");
    //client.println("Connection: close");
     if (client.available()) {
    char c = client.read();
    Serial.print(c);
  }
  }
  else {
    // kf you didn't get a connection to the server:
    Serial.println("connection failed");
  }
    
    //write fields one by one
   /* ThingSpeak.setField(1,Temp);
    ThingSpeak.setField(2,Hum);
    ThingSpeak.setField(3,Hindex);
    ThingSpeak.setField(4,Dpoint);
    ThingSpeak.setField(5,CHeat);
    //send fields to ThingSpeak 
    ThingSpeak.writeFields(ChannelNumber, writeAPIKey);  
    //ThingSpeak.writeField(ChannelNumber, 1, Temp, writeAPIKey);
    Serial.print("Data sent to IOT server");*/
}


// returns the number of button pressed
int buttonPress(int Pin){
  button = analogRead(Pin);
  if (button < 900){ 
    lastButton = button;
  } 
}

//LOOP:
void loop()
{
  while(true){ // i might not need this while loop...
  //wait the correct time to get the data from the sensor  
    delay(dht.getMinimumSamplingPeriod());
  //lcd.clear();
    //read new values from sensor
    float newHumidity = dht.getHumidity();
    float newTemperature = dht.getTemperature();
  
 /* 
  //some test data, if sensor is not attached
  float newHumidity = 65.38;
  float newTemperature = 22.45;
 
  */
  // only do the calculation of dew point and heat index if the values changed 
  if ((temperature != newTemperature) || (humidity != newHumidity)){
    
    //overwrite old values with new readings
    temperature = newTemperature;
    humidity = newHumidity;

    //calculate dewpoint and heat index
    heatIndex = getHeatIndex(temperature, humidity);
    dewPoint = getDewPoint(temperature, humidity);
  }
    
 //turn heating on if the temperature is less then the desired temperature
  if (temperature < desiredTemp) { 
    heating = true;
    //TODO: add heat time to heating hours  
  }

 //turn heating off if the temperature is more then the desired temperature + the tereshold 
  if (temperature > desiredTemp + tereshold) { 
    heating = false; 
  }    
  
 if (heating) {
  // TODO : turn relay pin on }
 }

  // button = 0*/+    <---whats this????
  
//Printing data several ways:
  //print data to the serial port 
  printDataToSerial(temperature,humidity,heatIndex,dewPoint);
  //print to LCD
  printMainScreenOnLCD(temperature,humidity,heatIndex,dewPoint,(boolean)1,"", 200);
  //Send data to the server to publish on HTTP
  //sendDataToServer(temperature,humidity,heatIndex,dewPoint,(boolean)1);
  //send data to IOT server
  // ThingSpeak will only accept updates every 15 seconds. 
  time = millis();
  if ( (time % 20000 ) > 15000){
     sendDataToIOT(temperature,humidity,heatIndex,dewPoint,(boolean)1);
  }
    
  //just testing the buttons functioning.Menu might not be implemented due to the lack of pins
    if ((lastButton > 60) && (lastButton < 200)){ //up button
       digitalWrite(BACKLIT_PIN,HIGH);
       }
    if ((lastButton > 200) && (lastButton < 400)){ //down button
       digitalWrite(BACKLIT_PIN,LOW);     
    }
  }
}

