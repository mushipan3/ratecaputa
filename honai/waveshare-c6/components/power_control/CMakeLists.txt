idf_component_register(SRCS "power_control.c"
                    INCLUDE_DIRS "include"
                    REQUIRES pcf8574 esp_driver_i2c)
