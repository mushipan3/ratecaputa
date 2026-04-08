#include "pcf8574.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"

static const char *TAG = "pcf8574";

esp_err_t pcf8574_init(pcf8574_t *dev, i2c_master_bus_handle_t bus, uint8_t addr)
{
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        .scl_speed_hz = 100000,
    };
    esp_err_t ret = i2c_master_bus_add_device(bus, &cfg, &dev->dev_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to add PCF8574 device: %s", esp_err_to_name(ret));
        return ret;
    }
    // 全ピンをHIGH（リレーOFF、アクティブLOW想定）
    dev->output_state = 0xFF;
    return i2c_master_transmit(dev->dev_handle, &dev->output_state, 1, pdMS_TO_TICKS(100));
}

esp_err_t pcf8574_set_pin(pcf8574_t *dev, uint8_t pin, bool level)
{
    if (pin > 7) return ESP_ERR_INVALID_ARG;
    if (level) {
        dev->output_state |= (1 << pin);
    } else {
        dev->output_state &= ~(1 << pin);
    }
    return i2c_master_transmit(dev->dev_handle, &dev->output_state, 1, pdMS_TO_TICKS(100));
}

esp_err_t pcf8574_get_state(pcf8574_t *dev, uint8_t *state)
{
    *state = dev->output_state;
    return ESP_OK;
}
