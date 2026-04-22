#include "kbd_scanner.h"
#include "esp_log.h"

#define TAG "kbd_scanner"
#define KBD_I2C_TIMEOUT_MS  10

static i2c_master_dev_handle_t s_dev_handle;

esp_err_t kbd_scanner_init(i2c_master_bus_handle_t bus)
{
    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = KBD_SCANNER_I2C_ADDR,
        .scl_speed_hz    = 100000,
    };
    esp_err_t ret = i2c_master_bus_add_device(bus, &dev_cfg, &s_dev_handle);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "kbd_scanner initialized (I2C addr=0x%02X)", KBD_SCANNER_I2C_ADDR);
    }
    return ret;
}

esp_err_t kbd_scanner_poll(kbd_key_event_t *event)
{
    uint8_t buf[2] = {0};

    esp_err_t ret = i2c_master_receive(s_dev_handle, buf, sizeof(buf), KBD_I2C_TIMEOUT_MS);
    if (ret != ESP_OK) {
        return ESP_ERR_NOT_FOUND;
    }

    if (buf[0] == 0x00) {
        return ESP_ERR_NOT_FOUND;
    }

    event->keycode = buf[0];
    event->pressed = buf[1];
    return ESP_OK;
}
