/**
 * I2C Scanner for Waveshare ESP32-C6 Touch LCD
 *
 * Scans all 7-bit I2C addresses and prints a table similar to `i2cdetect`.
 * Known devices on this board are labeled automatically.
 *
 * I2C pins: SDA=GPIO18, SCL=GPIO19
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2c_master.h"
#include "esp_log.h"

static const char *TAG = "i2c_scan";

#define I2C_SDA_GPIO    18
#define I2C_SCL_GPIO    19
#define I2C_PORT        0
#define I2C_PROBE_TIMEOUT_MS  50

/* Known device table */
typedef struct {
    uint8_t     addr;
    const char *name;
} known_device_t;

static const known_device_t known_devices[] = {
    { 0x20, "PCF8574 I/O expander (A2=A1=A0=0)" },
    { 0x21, "PCF8574 I/O expander (A2=A1=A0=1)" },
    { 0x22, "PCF8574 I/O expander (A2=A1=A0=2)" },
    { 0x23, "PCF8574 I/O expander (A2=A1=A0=3)" },
    { 0x24, "PCF8574 I/O expander (A2=A1=A0=4)" },
    { 0x25, "PCF8574 I/O expander (A2=A1=A0=5)" },
    { 0x26, "PCF8574 I/O expander (A2=A1=A0=6)" },
    { 0x27, "PCF8574 I/O expander (A2=A1=A0=7)" },
    { 0x38, "PCF8574A I/O expander (A2=A1=A0=0)" },
    { 0x3C, "SSD1306/SH1106 OLED display" },
    { 0x3D, "SSD1306/SH1106 OLED display" },
    { 0x48, "ADS1115 / TMP102 ADC/temp sensor" },
    { 0x57, "BQ27220 battery gauge" },
    { 0x63, "AXS5106 touch controller (on-board)" },
    { 0x68, "MPU6050 IMU / DS3231 RTC" },
    { 0x6A, "QMI8658 IMU" },
    { 0x6B, "QMI8658 IMU (on-board)" },
    { 0x76, "BMP280/BME280 pressure sensor" },
    { 0x77, "BMP280/BME280 pressure sensor" },
};
#define KNOWN_DEVICE_COUNT (sizeof(known_devices) / sizeof(known_devices[0]))

static const char *lookup_device(uint8_t addr)
{
    for (int i = 0; i < (int)KNOWN_DEVICE_COUNT; i++) {
        if (known_devices[i].addr == addr) {
            return known_devices[i].name;
        }
    }
    return NULL;
}

void app_main(void)
{
    /* Short delay so UART is ready */
    vTaskDelay(pdMS_TO_TICKS(500));

    ESP_LOGI(TAG, "=== I2C Scanner ===");
    ESP_LOGI(TAG, "SDA=GPIO%d  SCL=GPIO%d", I2C_SDA_GPIO, I2C_SCL_GPIO);

    /* Initialize I2C master bus */
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port            = (i2c_port_num_t)I2C_PORT,
        .sda_io_num          = I2C_SDA_GPIO,
        .scl_io_num          = I2C_SCL_GPIO,
        .clk_source          = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt   = 7,
        .flags.enable_internal_pullup = true,
    };
    i2c_master_bus_handle_t bus_handle;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus_handle));

    /* --- i2cdetect style table ---
     * Rows: upper nibble (0x0_ .. 0x7_)
     * Cols: lower nibble (0..f)
     */
    printf("\n     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n");

    int found_count = 0;

    for (int row = 0; row < 8; row++) {
        printf("%02x: ", row << 4);
        for (int col = 0; col < 16; col++) {
            uint8_t addr = (uint8_t)((row << 4) | col);

            /* Skip reserved addresses (0x00-0x07 and 0x78-0x7F) */
            if (addr < 0x08 || addr > 0x77) {
                printf("   ");
                continue;
            }

            esp_err_t ret = i2c_master_probe(bus_handle, addr, I2C_PROBE_TIMEOUT_MS);
            if (ret == ESP_OK) {
                printf("%02x ", addr);
                found_count++;
            } else {
                printf("-- ");
            }
        }
        printf("\n");
    }

    printf("\n");
    ESP_LOGI(TAG, "Scan complete. %d device(s) found.\n", found_count);

    /* --- Detailed report --- */
    if (found_count > 0) {
        printf("Address  Device\n");
        printf("-------  ------\n");
        for (int row = 0; row < 8; row++) {
            for (int col = 0; col < 16; col++) {
                uint8_t addr = (uint8_t)((row << 4) | col);
                if (addr < 0x08 || addr > 0x77) {
                    continue;
                }
                esp_err_t ret = i2c_master_probe(bus_handle, addr, I2C_PROBE_TIMEOUT_MS);
                if (ret == ESP_OK) {
                    const char *name = lookup_device(addr);
                    if (name) {
                        printf("0x%02X     %s\n", addr, name);
                    } else {
                        printf("0x%02X     (unknown device)\n", addr);
                    }
                }
            }
        }
        printf("\n");
    }

    ESP_ERROR_CHECK(i2c_del_master_bus(bus_handle));
    ESP_LOGI(TAG, "Done.");
}
