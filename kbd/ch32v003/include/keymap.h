#pragma once

/*
 * ラテカピュータ オリジナルキーボード キーマップ定義
 *
 * ABCDEFG配列 + モード切り替えスイッチ
 * キーマトリクスのROW/COLは実機確認後に定義する
 */

// キーマトリクス サイズ
// ROW: PC0,PC3,PC4,PC5,PC6,PC7,PD0 = 7本
// COL: PA1,PA2,PD2,PD3,PD4,PD5,PD6,PD7 = 8本
// → 最大 7×8 = 56キー (実際のキー数確定後にマッピングテーブルを埋める)
// ※ PC1(SDA)/PC2(SCL) はI2C用に予約、PD1(SWIO) は書き込み用に予約
#define KBD_ROWS   7
#define KBD_COLS   8

// キーコード定義 (ABCDEFG順)
// 0x00 = イベントなし
#define KEY_NONE   0x00

// アルファベット (A=0x41 ... Z=0x5A, ASCII準拠)
#define KEY_A      0x41
#define KEY_B      0x42
#define KEY_C      0x43
#define KEY_D      0x44
#define KEY_E      0x45
#define KEY_F      0x46
#define KEY_G      0x47
#define KEY_H      0x48
#define KEY_I      0x49
#define KEY_J      0x4A
#define KEY_K      0x4B
#define KEY_L      0x4C
#define KEY_M      0x4D
#define KEY_N      0x4E
#define KEY_O      0x4F
#define KEY_P      0x50
#define KEY_Q      0x51
#define KEY_R      0x52
#define KEY_S      0x53
#define KEY_T      0x54
#define KEY_U      0x55
#define KEY_V      0x56
#define KEY_W      0x57
#define KEY_X      0x58
#define KEY_Y      0x59
#define KEY_Z      0x5A

// 数字
#define KEY_0      0x30
#define KEY_1      0x31
#define KEY_2      0x32
#define KEY_3      0x33
#define KEY_4      0x34
#define KEY_5      0x35
#define KEY_6      0x36
#define KEY_7      0x37
#define KEY_8      0x38
#define KEY_9      0x39

// 特殊キー (0x80以降)
#define KEY_ENTER  0x80
#define KEY_SPACE  0x81
#define KEY_BS     0x82
#define KEY_ESC    0x83
#define KEY_SHIFT  0x90
#define KEY_CTRL   0x91
// モード切り替えスイッチ (シャープポケコン方式)
#define KEY_MODE_BASIC   0xA0
#define KEY_MODE_KANA    0xA1
#define KEY_MODE_SYMBOL  0xA2

/*
 * キーマトリクス GPIO配線
 *
 * UIAPduino Pro (CH32V003F4P6) ピン対応:
 *   Arduino pin → CH32V003 GPIO
 *   pin2=PC0, pin3=PC1(SDA), pin4=PC2(SCL), pin5=PC3
 *   pin7=PC5, pin8=PC6, pin9=PC7, pin10=PD0, pin11=PD1(SWIO)
 *   A0=PA2, A1=PA1, A2=PC4, A3=PD2, A4=PD3, A5=PD5, A6=PD6, A7=PD4, pin17=PD7
 *
 * ROW (出力 / LOW アクティブ):
 *   R0=PC0, R1=PC3, R2=PC4, R3=PC5, R4=PC6, R5=PC7, R6=PD0
 *
 * COL (入力プルアップ / LOW=押下):
 *   C0=PA1, C1=PA2, C2=PD2, C3=PD3, C4=PD4, C5=PD5, C6=PD6, C7=PD7
 *
 * 予約済み: PC1(SDA), PC2(SCL) → I2C / PD1(SWIO) → 書き込み用
 */

// ROW ポート・ビット定義
#define ROW_PORT_C_MASK  (GPIO_Pin_0 | GPIO_Pin_3 | GPIO_Pin_4 | GPIO_Pin_5 | GPIO_Pin_6 | GPIO_Pin_7)
#define ROW_PORT_D_MASK  (GPIO_Pin_0)

static const struct { GPIO_TypeDef *port; uint16_t pin; } kbd_rows[KBD_ROWS] = {
    { GPIOC, GPIO_Pin_0 },  // R0: PC0
    { GPIOC, GPIO_Pin_3 },  // R1: PC3
    { GPIOC, GPIO_Pin_4 },  // R2: PC4
    { GPIOC, GPIO_Pin_5 },  // R3: PC5
    { GPIOC, GPIO_Pin_6 },  // R4: PC6
    { GPIOC, GPIO_Pin_7 },  // R5: PC7
    { GPIOD, GPIO_Pin_0 },  // R6: PD0
};

static const struct { GPIO_TypeDef *port; uint16_t pin; } kbd_cols[KBD_COLS] = {
    { GPIOA, GPIO_Pin_1 },  // C0: PA1
    { GPIOA, GPIO_Pin_2 },  // C1: PA2
    { GPIOD, GPIO_Pin_2 },  // C2: PD2
    { GPIOD, GPIO_Pin_3 },  // C3: PD3
    { GPIOD, GPIO_Pin_4 },  // C4: PD4
    { GPIOD, GPIO_Pin_5 },  // C5: PD5
    { GPIOD, GPIO_Pin_6 },  // C6: PD6
    { GPIOD, GPIO_Pin_7 },  // C7: PD7
};

/*
 * キーマトリクス マッピングテーブル [ROW][COL]
 * 実機のキー配置が確定したら埋める (現在はプレースホルダ)
 */
static const uint8_t keymap_matrix[KBD_ROWS][KBD_COLS] = {
    /* COL:   C0       C1       C2       C3       C4       C5       C6       C7    */
    /* R0 */ { KEY_A,  KEY_B,   KEY_C,   KEY_D,   KEY_E,   KEY_F,   KEY_G,   KEY_NONE },
    /* R1 */ { KEY_H,  KEY_I,   KEY_J,   KEY_K,   KEY_L,   KEY_M,   KEY_N,   KEY_NONE },
    /* R2 */ { KEY_O,  KEY_P,   KEY_Q,   KEY_R,   KEY_S,   KEY_T,   KEY_U,   KEY_NONE },
    /* R3 */ { KEY_V,  KEY_W,   KEY_X,   KEY_Y,   KEY_Z,   KEY_1,   KEY_2,   KEY_3   },
    /* R4 */ { KEY_4,  KEY_5,   KEY_6,   KEY_7,   KEY_8,   KEY_9,   KEY_0,   KEY_NONE },
    /* R5 */ { KEY_ENTER,KEY_SPACE,KEY_BS,KEY_ESC, KEY_NONE,KEY_NONE,KEY_NONE,KEY_NONE },
    /* R6 */ { KEY_SHIFT,KEY_CTRL,KEY_MODE_BASIC,KEY_MODE_KANA,KEY_MODE_SYMBOL,KEY_NONE,KEY_NONE,KEY_NONE },
};
