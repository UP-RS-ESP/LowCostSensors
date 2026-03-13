#include <Wire.h>
#include <Adafruit_MCP9808.h>

//#define TF02_I2C_ADDRESS 0x10 // I2C address of the TF02 Pro LiDAR
//#define I2C_BUFFER_SIZE 32    // Adjust the buffer size as needed
#define NUM_SAMPLES 10        // Number of samples to average over one second
#define SAMPLE_INTERVAL 1000  // Milliseconds for one-second sampling
#define MAX_DISTANCE 4499     // Maximum valid distance
//NOTE: For unreliable data (signal strength less than 60) or far data (distance greater 45m), default value is 4500. To protect averages, these data are now ignored
#define MCP9808_I2C_ADDRESS 0x18 // I2C address of the MCP9808 temperature sensor

struct LiDARData {
  unsigned int distance;
  unsigned int signalStrength;
};

LiDARData samples[NUM_SAMPLES];
unsigned int currentIndex = 0;
unsigned int sumDistance = 0;
unsigned int sumSignalStrength = 0;
unsigned long lastSampleTime = 0;

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200); // Hardware Serial1 for TF02 Pro LiDAR
  
  //Serial.println("TF02 Pro LiDAR Data Logger");
  if (!tempsensor.begin(MCP9808_I2C_ADDRESS)) {
    Serial.println("Couldn't find MCP9808!");
    while (1);
  }

  // Configure TF02 Pro LiDAR
  Serial1.write(0x42); // Command to start measurement
}

void loop() {
  if (Serial1.available() >= 9) {
    if (Serial1.read() == 0x59 && Serial1.read() == 0x59) {
      LiDARData data;
      data.distance = Serial1.read() + Serial1.read() * 256;
      data.signalStrength = Serial1.read();

      // Check if the distance is valid (less than or equal to MAX_DISTANCE)
      if (data.distance <= MAX_DISTANCE) {
        // You can use data.distance and data.signalStrength here or print them to the Serial Monitor
        //Serial.print("Distance: ");
        //Serial.print(data.distance);
        //Serial.println(" mm");
        //Serial.print("Signal Strength: ");
        //Serial.println(data.signalStrength);

        // Calculate the average distance and signal strength
        sumDistance -= samples[currentIndex].distance;
        sumSignalStrength -= samples[currentIndex].signalStrength;

        samples[currentIndex] = data;

        sumDistance += data.distance;
        sumSignalStrength += data.signalStrength;

        currentIndex = (currentIndex + 1) % NUM_SAMPLES;

        // If one second has elapsed, calculate and print the average distance and signal strength
        if (millis() - lastSampleTime >= SAMPLE_INTERVAL) {
          float averageDistance = static_cast<float>(sumDistance) / NUM_SAMPLES;
          float averageSignalStrength = static_cast<float>(sumSignalStrength) / NUM_SAMPLES;
          Serial.print("Nr Samp: ");
          Serial.print(NUM_SAMPLES);
          Serial.print(", Avg Dist (1s): ");
          Serial.print(averageDistance);
          Serial.print(" mm, Avg Signal Str: ");
          Serial.print(averageSignalStrength);
          float temperature = tempsensor.readTempC();
          Serial.print(", Temp(C): ");
          Serial.println(temperature);
          lastSampleTime = millis();
        }
      }
    }
  }
}
