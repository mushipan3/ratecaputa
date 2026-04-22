/*
 * I2C接続検証用 main.c
 * ESP32-C6 (マスタ) → CH32V003 (スレーブ 0x08) から2バイト読み取り、ログ出力する
 */
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

#include "bsp_i2c.h"
#include "kbd_scanner.h"

#define TAG "main"

void app_main(void)
{
    // I2C初期化
    i2c_master_bus_handle_t i2c_bus;
    ESP_ERROR_CHECK(bsp_i2c_init(&i2c_bus));
    ESP_LOGI(TAG, "I2C master initialized (SDA=GPIO18, SCL=GPIO19)");

    // キースキャナ初期化
    ESP_ERROR_CHECK(kbd_scanner_init(i2c_bus));

    ESP_LOGI(TAG, "I2C verification started. Reading from CH32V003 (addr=0x%02X)...", KBD_SCANNER_I2C_ADDR);

    // 検証ループ: 500msごとに読み取り
    kbd_key_event_t event;
    uint32_t count = 0;
    while (1) {
        esp_err_t ret = kbd_scanner_poll(&event);
        if (ret == ESP_OK) {
            ESP_LOGI(TAG, "[%lu] keycode=0x%02X pressed=%d", count, event.keycode, event.pressed);
        } else {
            ESP_LOGI(TAG, "[%lu] no event (0x00, 0x00)", count);
        }
        count++;
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
