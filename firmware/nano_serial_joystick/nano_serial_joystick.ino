#include <Arduino.h>

// -------- Pin mapping --------
const uint8_t BTN1_PIN = 12;
const uint8_t BTN2_PIN = 10;
const uint8_t BTN3_PIN = 11;
const uint8_t BTN4_PIN = 9;

const uint8_t STICK1_X_PIN = 14;
const uint8_t STICK1_Y_PIN = 15;
const uint8_t STICK2_X_PIN = 16;
const uint8_t STICK2_Y_PIN = 17;

// -------- Serial settings --------
const unsigned long SERIAL_BAUD = 230400;
const unsigned long KEEPALIVE_MS = 50;
const uint16_t AXIS_CHANGE_THRESHOLD = 3;
const uint8_t AXIS_FILTER_SAMPLES = 4;
const unsigned long DEBOUNCE_MS = 8;

struct ButtonState {
  uint8_t pin;
  bool stableState;
  bool lastRead;
  unsigned long lastChangeMs;
};

ButtonState buttons[4] = {
  {BTN1_PIN, false, false, 0},
  {BTN2_PIN, false, false, 0},
  {BTN3_PIN, false, false, 0},
  {BTN4_PIN, false, false, 0}
};

const uint8_t axisPins[4] = {STICK1_X_PIN, STICK1_Y_PIN, STICK2_X_PIN, STICK2_Y_PIN};
int filteredAxes[4] = {0, 0, 0, 0};
int lastSentAxes[4] = {-1, -1, -1, -1};
bool lastSentButtons[4] = {false, false, false, false};
unsigned long lastTransmitMs = 0;

int readFilteredAxis(uint8_t pin) {
  long sum = 0;
  for (uint8_t i = 0; i < AXIS_FILTER_SAMPLES; ++i) {
    sum += analogRead(pin);
  }
  return (int)(sum / AXIS_FILTER_SAMPLES);
}

bool updateButton(ButtonState &button, unsigned long nowMs) {
  bool rawPressed = digitalRead(button.pin) == LOW;  // INPUT_PULLUP

  if (rawPressed != button.lastRead) {
    button.lastRead = rawPressed;
    button.lastChangeMs = nowMs;
  }

  if ((nowMs - button.lastChangeMs) >= DEBOUNCE_MS && button.stableState != rawPressed) {
    button.stableState = rawPressed;
    return true;
  }

  return false;
}

bool axesChangedEnough() {
  for (uint8_t i = 0; i < 4; ++i) {
    if (lastSentAxes[i] < 0 || abs(filteredAxes[i] - lastSentAxes[i]) >= AXIS_CHANGE_THRESHOLD) {
      return true;
    }
  }
  return false;
}

bool buttonsChanged() {
  for (uint8_t i = 0; i < 4; ++i) {
    if (buttons[i].stableState != lastSentButtons[i]) {
      return true;
    }
  }
  return false;
}

void transmitState(unsigned long nowMs) {
  Serial.print("T,");
  for (uint8_t i = 0; i < 4; ++i) {
    Serial.print(buttons[i].stableState ? 1 : 0);
    Serial.print(',');
    lastSentButtons[i] = buttons[i].stableState;
  }

  for (uint8_t i = 0; i < 4; ++i) {
    Serial.print(filteredAxes[i]);
    lastSentAxes[i] = filteredAxes[i];
    if (i < 3) {
      Serial.print(',');
    }
  }
  Serial.println();
  lastTransmitMs = nowMs;
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  for (uint8_t i = 0; i < 4; ++i) {
    pinMode(buttons[i].pin, INPUT_PULLUP);
    buttons[i].stableState = digitalRead(buttons[i].pin) == LOW;
    buttons[i].lastRead = buttons[i].stableState;
    buttons[i].lastChangeMs = millis();
  }

  for (uint8_t i = 0; i < 4; ++i) {
    filteredAxes[i] = readFilteredAxis(axisPins[i]);
    lastSentAxes[i] = filteredAxes[i];
    lastSentButtons[i] = buttons[i].stableState;
  }

  transmitState(millis());
}

void loop() {
  unsigned long nowMs = millis();
  bool anyButtonChanged = false;

  for (uint8_t i = 0; i < 4; ++i) {
    if (updateButton(buttons[i], nowMs)) {
      anyButtonChanged = true;
    }
  }

  for (uint8_t i = 0; i < 4; ++i) {
    filteredAxes[i] = readFilteredAxis(axisPins[i]);
  }

  bool sendDueToChange = anyButtonChanged || axesChangedEnough() || buttonsChanged();
  bool sendDueToKeepalive = (nowMs - lastTransmitMs) >= KEEPALIVE_MS;

  if (sendDueToChange || sendDueToKeepalive) {
    transmitState(nowMs);
  }
}
