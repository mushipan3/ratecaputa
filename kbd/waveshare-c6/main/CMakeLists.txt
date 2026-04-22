idf_component_register(SRCS "main.c" "lv_font_jp_16.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp_bsp kbd_scanner lvgl__lvgl)

target_compile_definitions(__idf_main PRIVATE LV_LVGL_H_INCLUDE_SIMPLE)
