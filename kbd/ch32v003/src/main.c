/*
 * latecaputa-kbd / CH32V003 I2C接続検証用スレーブ
 *
 * I2C設定:
 *   - アドレス : 0x08
 *   - SDA      : PC1 (pin3)
 *   - SCL      : PC2 (pin4)
 *   - 応答フォーマット: [counter(1byte), 0x55]
 *     counterはマスターから読まれるたびにインクリメントする
 *     ESP32-C6側のログで数値が増えていれば通信成功
 */

#include "ch32v00x.h"
#include "ch32v00x_i2c.h"
#include "ch32v00x_gpio.h"
#include "ch32v00x_rcc.h"
#include "debug.h"

#define I2C_SLAVE_ADDR   0x08

// ---- I2C スレーブ応答バッファ ----
// buf[0]: カウンタ（読まれるたびにインクリメント）
// buf[1]: 固定値 0x55（通信確認用マーカー）
static volatile uint8_t tx_buf[2] = {0x00, 0x55};
static volatile uint8_t tx_idx = 0;

static void i2c_slave_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    I2C_InitTypeDef  i2c  = {0};

    // I2C1 クロック有効化
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1,  ENABLE);

    // PC1=SDA, PC2=SCL: オープンドレイン AF
    gpio.GPIO_Pin   = GPIO_Pin_1 | GPIO_Pin_2;
    gpio.GPIO_Mode  = GPIO_Mode_AF_OD;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &gpio);

    // I2C1 スレーブ設定
    i2c.I2C_Mode                = I2C_Mode_I2C;
    i2c.I2C_DutyCycle           = I2C_DutyCycle_2;
    i2c.I2C_OwnAddress1         = I2C_SLAVE_ADDR << 1;
    i2c.I2C_Ack                 = I2C_Ack_Enable;
    i2c.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
    i2c.I2C_ClockSpeed          = 100000;
    I2C_Init(I2C1, &i2c);
    I2C_Cmd(I2C1, ENABLE);

    // I2Cイベント割り込み有効化
    NVIC_EnableIRQ(I2C1_EV_IRQn);
    I2C_ITConfig(I2C1, I2C_IT_EVT | I2C_IT_BUF, ENABLE);
}

// ---- I2C 割り込みハンドラ (スレーブ送信) ----
void I2C1_EV_IRQHandler(void) __attribute__((interrupt));
void I2C1_EV_IRQHandler(void)
{
    uint32_t event = I2C_GetLastEvent(I2C1);

    // マスターから読み出し要求 (アドレス一致・送信方向)
    if (event == I2C_EVENT_SLAVE_TRANSMITTER_ADDRESS_MATCHED) {
        tx_idx = 0;
        I2C_SendData(I2C1, tx_buf[tx_idx++]);
    }
    // 続きのバイト送信要求
    else if (event == I2C_EVENT_SLAVE_BYTE_TRANSMITTED) {
        if (tx_idx < 2) {
            I2C_SendData(I2C1, tx_buf[tx_idx++]);
        } else {
            I2C_SendData(I2C1, 0x00);
        }
    }
    // ストップ検出: カウンタをインクリメントして次の読み出しに備える
    else if (event == I2C_EVENT_SLAVE_STOP_DETECTED) {
        tx_buf[0]++;
        I2C_Cmd(I2C1, ENABLE);
    }
}

// ---- メイン ----
int main(void)
{
    SystemInit();
    i2c_slave_init();

    // 検証ループ: I2C割り込みに任せるだけ、メインループは何もしない
    while (1) {
        Delay_Ms(100);
    }

    return 0;
}
