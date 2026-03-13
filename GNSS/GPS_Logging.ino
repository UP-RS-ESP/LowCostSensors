#define GPSSerial Serial1

void setup() {
  // make this baud rate fast enough to we aren't waiting on it
  Serial.begin(115200);

  // wait for hardware serial to appear
  while (!Serial) delay(1000);

  // 9600 baud is the default rate for the Ultimate GPS
  GPSSerial.begin(9600);

  //Set the update rate to 1Hz
  GPSSerial.println("$PMTK220,1000*1F\r\n");

  // PMTK_SET_NMEA_OUTPUT_RMCGGAGSV: (Drop VTG -- don't need velocity)
  GPSSerial.println("$PMTK314,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0*29");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    GPSSerial.write(c);
    GPSSerial.flush(); //Added this to ensure no mixed lines
  }
  if (GPSSerial.available()) {
    char c = GPSSerial.read();
    Serial.write(c);
    Serial.flush(); //Added this to ensure no mixed lines
  }
}
