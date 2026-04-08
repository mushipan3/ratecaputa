#include <stdio.h>
#include "esp_err.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_lvgl_port.h"
#include "bsp_display.h"
#include "bsp_touch.h"
#include "bsp_i2c.h"
#include "bsp_spi.h"
#include "power_control.h"

static const char *TAG = "ratecaputa";

// ランドスケープ（90°回転）: 320x172
#define LCD_H_RES              320
#define LCD_V_RES              172
#define LCD_DRAW_BUFF_HEIGHT   50
#define LCD_DRAW_BUFF_DOUBLE   1

static esp_lcd_panel_io_handle_t io_handle    = NULL;
static esp_lcd_panel_handle_t   panel_handle  = NULL;
static esp_lcd_touch_handle_t   touch_handle  = NULL;
static lv_display_t            *lvgl_disp     = NULL;
static lv_indev_t              *lvgl_touch_indev = NULL;

// 日本語フォント（lv_font_jp_16.cで定義）
LV_FONT_DECLARE(lv_font_jp_16);

static const char *CH_NAMES[POWER_CH_MAX] = {
    "ラテカセ本体",
    "スイッチ電源",
    "Windows",
    "Raspberry Pi",
};

static lv_obj_t *btn_list[POWER_CH_MAX];

static void btn_event_cb(lv_event_t *e)
{
    lv_obj_t *btn = lv_event_get_target(e);
    power_channel_t ch = (power_channel_t)(uintptr_t)lv_event_get_user_data(e);

    bool next = !power_control_get(ch);
    power_control_set(ch, next);

    lv_obj_set_style_bg_color(btn, next ? lv_color_hex(0x2196F3) : lv_color_hex(0x555555), LV_PART_MAIN);
    ESP_LOGI(TAG, "%s -> %s", CH_NAMES[ch], next ? "ON" : "OFF");
}

static void create_power_ui(void)
{
    lv_obj_t *scr = lv_scr_act();
    lv_obj_set_style_bg_color(scr, lv_color_hex(0x1a1a2e), LV_PART_MAIN);

    // タイトル
    lv_obj_t *title = lv_label_create(scr);
    lv_label_set_text(title, "電源管理");
    lv_obj_set_style_text_color(title, lv_color_hex(0xFFFFFF), LV_PART_MAIN);
    lv_obj_set_style_text_font(title, &lv_font_jp_16, LV_PART_MAIN);
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 6);

    // 2x2グリッドボタン（ランドスケープ 320x172）
    // ボタンサイズ: 140x58、マージン: 10px
    const int BTN_W = 140;
    const int BTN_H = 58;
    const int COL_OFFSET = 80;  // 中心からの横オフセット
    const int ROW1_Y = 42;
    const int ROW2_Y = 108;

    int positions[POWER_CH_MAX][2] = {
        {-COL_OFFSET, ROW1_Y},  // CH0: 左上
        { COL_OFFSET, ROW1_Y},  // CH1: 右上
        {-COL_OFFSET, ROW2_Y},  // CH2: 左下
        { COL_OFFSET, ROW2_Y},  // CH3: 右下
    };

    for (int i = 0; i < POWER_CH_MAX; i++) {
        lv_obj_t *btn = lv_btn_create(scr);
        lv_obj_set_size(btn, BTN_W, BTN_H);
        lv_obj_align(btn, LV_ALIGN_TOP_MID, positions[i][0], positions[i][1]);
        lv_obj_set_style_bg_color(btn, lv_color_hex(0x555555), LV_PART_MAIN);
        lv_obj_set_style_radius(btn, 8, LV_PART_MAIN);
        lv_obj_add_event_cb(btn, btn_event_cb, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
        btn_list[i] = btn;

        lv_obj_t *label = lv_label_create(btn);
        lv_label_set_text(label, CH_NAMES[i]);
        lv_obj_set_style_text_color(label, lv_color_hex(0xFFFFFF), LV_PART_MAIN);
        lv_obj_set_style_text_font(label, &lv_font_jp_16, LV_PART_MAIN);
        lv_obj_center(label);
    }
}

static esp_err_t app_lvgl_init(void)
{
    const lvgl_port_cfg_t lvgl_cfg = {
        .task_priority     = 4,
        .task_stack        = 1024 * 10,
        .task_affinity     = -1,
        .task_max_sleep_ms = 500,
        .timer_period_ms   = 5,
    };
    ESP_RETURN_ON_ERROR(lvgl_port_init(&lvgl_cfg), TAG, "LVGL port init failed");

    lvgl_port_display_cfg_t disp_cfg = {
        .io_handle     = io_handle,
        .panel_handle  = panel_handle,
        .buffer_size   = LCD_H_RES * LCD_DRAW_BUFF_HEIGHT,
        .double_buffer = LCD_DRAW_BUFF_DOUBLE,
        .hres          = LCD_H_RES,
        .vres          = LCD_V_RES,
        .monochrome    = false,
        // 90°回転: swap_xy=true, mirror_x=true
        .rotation      = { .swap_xy = true, .mirror_x = true, .mirror_y = false },
        .flags         = { .buff_dma = true,
#if LVGL_VERSION_MAJOR >= 9
                           .swap_bytes = true,
#endif
        },
    };
    // 90°回転時のパネルギャップ
    ESP_ERROR_CHECK(esp_lcd_panel_set_gap(panel_handle, 0, 34));
    lvgl_disp = lvgl_port_add_disp(&disp_cfg);

    const lvgl_port_touch_cfg_t touch_cfg = {
        .disp   = lvgl_disp,
        .handle = touch_handle,
    };
    lvgl_touch_indev = lvgl_port_add_touch(&touch_cfg);

    return ESP_OK;
}

void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    i2c_master_bus_handle_t i2c_bus = bsp_i2c_init();
    bsp_spi_init();
    bsp_display_init(&io_handle, &panel_handle, LCD_H_RES * LCD_DRAW_BUFF_HEIGHT);
    bsp_touch_init(&touch_handle, i2c_bus, LCD_H_RES, LCD_V_RES, 90);

    if (power_control_init(i2c_bus) != ESP_OK) {
        ESP_LOGW(TAG, "PCF8574 not found - relay control disabled");
    }
    ESP_ERROR_CHECK(app_lvgl_init());

    bsp_display_brightness_init();
    bsp_display_set_brightness(100);

    if (lvgl_port_lock(0)) {
        create_power_ui();
        lvgl_port_unlock();
    }

    ESP_LOGI(TAG, "Ratecaputa power control started");
}
