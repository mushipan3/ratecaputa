#pragma once

#include "esp_err.h"
#include "esp_check.h"
#include "driver/i2c_master.h"

// 電源チャンネル定義
typedef enum {
    POWER_CH_LATECASSE  = 0,  // CH1: ラテカセ本体
    POWER_CH_SWITCHING  = 1,  // CH2: スイッチ電源（FDD 12V等）
    POWER_CH_WINDOWS    = 2,  // CH3: USB電源 Windows系統
    POWER_CH_RASPI      = 3,  // CH4: USB電源 Raspberry Pi系統
    POWER_CH_MAX        = 4,
} power_channel_t;

esp_err_t power_control_init(i2c_master_bus_handle_t bus);
esp_err_t power_control_set(power_channel_t ch, bool on);
bool      power_control_get(power_channel_t ch);
