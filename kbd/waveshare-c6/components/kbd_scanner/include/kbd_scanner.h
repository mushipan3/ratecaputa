#pragma once

#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c_master.h"

#define KBD_SCANNER_I2C_ADDR  0x08

typedef struct {
    uint8_t keycode;
    uint8_t pressed;
} kbd_key_event_t;

esp_err_t kbd_scanner_init(i2c_master_bus_handle_t bus);
esp_err_t kbd_scanner_poll(kbd_key_event_t *event);
