#pragma once

#include "esp_err.h"
#include "driver/i2c_master.h"

#define PCF8574_I2C_ADDR_BASE 0x20  // A2=A1=A0=0

typedef struct {
    i2c_master_dev_handle_t dev_handle;
    uint8_t output_state;
} pcf8574_t;

esp_err_t pcf8574_init(pcf8574_t *dev, i2c_master_bus_handle_t bus, uint8_t addr);
esp_err_t pcf8574_set_pin(pcf8574_t *dev, uint8_t pin, bool level);
esp_err_t pcf8574_get_state(pcf8574_t *dev, uint8_t *state);
