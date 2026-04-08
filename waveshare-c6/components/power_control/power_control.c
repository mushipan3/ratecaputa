#include "power_control.h"
#include "pcf8574.h"
#include "esp_log.h"

static const char *TAG = "power_control";
static pcf8574_t s_pcf;

// PCF8574のピンとチャンネルのマッピング（アクティブLOWリレー想定）
static const uint8_t CH_PIN[POWER_CH_MAX] = {0, 1, 2, 3};

esp_err_t power_control_init(i2c_master_bus_handle_t bus)
{
    esp_err_t ret = pcf8574_init(&s_pcf, bus, PCF8574_I2C_ADDR_BASE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "PCF8574 init failed: %s", esp_err_to_name(ret));
    }
    return ret;
}

esp_err_t power_control_set(power_channel_t ch, bool on)
{
    if (ch >= POWER_CH_MAX) return ESP_ERR_INVALID_ARG;
    // アクティブLOW: ONのときピンをLOW
    return pcf8574_set_pin(&s_pcf, CH_PIN[ch], !on);
}

bool power_control_get(power_channel_t ch)
{
    if (ch >= POWER_CH_MAX) return false;
    uint8_t state;
    pcf8574_get_state(&s_pcf, &state);
    // アクティブLOW: ピンがLOWならON
    return !((state >> CH_PIN[ch]) & 0x01);
}
