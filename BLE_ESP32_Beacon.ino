#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>


#define BEACON_UUID "87b35b27-4a00-4740-928d-190696340f1a"
#define DEVICE_NAME "ESP32_Anchor_1" // Change for each anchor (1, 2, 3, 4)


void setup() {
  BLEDevice::init(DEVICE_NAME);
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
 
  BLEBeacon oBeacon = BLEBeacon();
  oBeacon.setManufacturerId(0x4C00);
  oBeacon.setProximityUUID(BLEUUID(BEACON_UUID));
  oBeacon.setMajor(1);
  oBeacon.setMinor(0);
  oBeacon.setSignalPower(-59);


  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  oAdvertisementData.setFlags(0x04);

  String strServiceData = "";
  strServiceData += (char)26;     // Len
  strServiceData += (char)0xFF;   // Type
  strServiceData += oBeacon.getData();
 
  oAdvertisementData.addData(strServiceData);
    // Set the advertising interval (500ms)
  // The value is in units of 0.625ms (500 / 0.625 = 800)
  pAdvertising->setMinInterval(160); //100 ms frequency
  pAdvertising->setMaxInterval(160);


  pAdvertising->setAdvertisementData(oAdvertisementData);
  pAdvertising->start();
 
}


void loop() {
  delay(1000); // Just broadcasting
}
