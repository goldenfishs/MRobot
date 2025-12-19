/*
    LCD驱动

高效：
--------控制引脚配置，屏幕属性配置完成后即可使用
可扩展：
--------添加你喜欢的颜色，
--------在lcd_library.h添加你的自定义点阵库-使用LCD_DrawBitmap驱动任意位图
兼容：
--------LSB与MSB顺序的字表

所有绘制函数使用示例：
LCD_DrawPoint(0,0,BLUE);
LCD_DrawChar(10, 10, 'A', RED, WHITE);
LCD_DrawLine(10, 10, 100, 50, RED);
LCD_DrawRectangle(10,10,50,100,GREEN);
LCD_DrawHollowCircle(200,50,16,RED);
LCD_DrawSolidCircle(200,100,16,RED);
LCD_DrawString(0,0,"MR16",MEDIUMORCHID,32,LSB);

extern const unsigned char logo_M[];
LCD_DrawBitmap(logo_M,70,70,64,64,MEDIUMORCHID,MSB);

*/

/* Includes ----------------------------------------------------------------- */
#include "device/lcd_driver/lcd.h"
#include "device/device.h"
#include "device/lcd_driver/lcd_lib.h"
#include "bsp/spi.h"

#include <stdlib.h>
#include <stdio.h>
/* USER INCLUDE BEGIN */

/* USER INCLUDE END */
/* Private define ----------------------------------------------------------- */

/* USER DEFINE BEGIN */

/* USER DEFINE END */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static LCD_Orientation_t lcd_orientation = LCD_ORIENTATION_PORTRAIT; // 当前屏幕方向

/* Private function  -------------------------------------------------------- */
/**
 * 写命令到LCD
 * 
 * @param cmd 要写入的命令
 * 
 * @note 此函数用于向LCD发送控制命令。通过设置数据/命令选择引脚为命令模式，
 *       并通过SPI接口发送命令。
 */
static int8_t LCD_WriteCommand(uint8_t cmd) {
    LCD_DC_LOW(); // 设置数据/命令选择引脚为命令模式
    LCD_CS_LOW(); // 使能SPI片选
    BSP_SPI_Transmit(BSP_SPI_LCD, &cmd, 1, false); // 通过SPI发送命令
    LCD_CS_HIGH(); // 禁用SPI片选
    return DEVICE_OK;
}

/**
 * 写数据到LCD
 * 
 * @param data 要写入的数据
 * 
 * @note 此函数用于向LCD发送数据。通过设置数据/命令选择引脚为数据模式，
 *       并通过SPI接口发送数据。
 */
static int8_t LCD_WriteData(uint8_t data) {
    LCD_DC_HIGH(); // 设置数据/命令选择引脚为数据模式
    LCD_CS_LOW(); // 使能SPI片选
    BSP_SPI_Transmit(BSP_SPI_LCD, &data, 1, false); // 通过SPI发送数据
    LCD_CS_HIGH(); // 禁用SPI片选
    return DEVICE_OK;
}

/**
 * 使用 DMA 写多个数据到 LCD
 * 
 * @param data 数据缓冲区指针
 * @param size 数据大小（字节数）
 * 
 * @note 此函数用于通过DMA快速发送大量数据到LCD。适用于数据量较大的场景，
 *       提高传输效率。
 */
static int8_t LCD_WriteDataBuffer_DMA(uint8_t *data, uint16_t size) {
    LCD_DC_HIGH(); // 设置数据/命令选择引脚为数据模式
    LCD_CS_LOW(); // 使能SPI片选
    BSP_SPI_Transmit(BSP_SPI_LCD, data, size, true); // 通过SPI发送数据
    while(BSP_SPI_GetState(BSP_SPI_LCD) != HAL_SPI_STATE_READY); // 等待SPI传输完成
    LCD_CS_HIGH(); // 禁用SPI片选
    return DEVICE_OK;
}

/**
 * 修改原来的 LCD_WriteDataBuffer，增加 DMA 支持
 * 
 * @param data 数据缓冲区指针
 * @param size 数据大小（字节数）
 * 
 * @note 此函数根据数据量大小选择使用DMA或普通SPI传输。如果数据量大于64字节，
 *       使用DMA传输，否则使用普通SPI传输。
 */
static int8_t LCD_WriteDataBuffer(uint8_t *data, uint16_t size) {
    if (size > 64) { // 如果数据量较大，使用 DMA
        LCD_WriteDataBuffer_DMA(data, size);
    } else { // 否则使用普通传输
        LCD_DC_HIGH(); // 设置数据/命令选择引脚为数据模式
        LCD_CS_LOW(); // 使能SPI片选
        BSP_SPI_Transmit(BSP_SPI_LCD, data, size, false); // 通过SPI发送数据
        LCD_CS_HIGH(); // 禁用SPI片选
    }
    return DEVICE_OK;
}

/**
 * 根据屏幕方向映射坐标
 * 
 * @param x 输入的X坐标
 * @param y 输入的Y坐标
 * @param mx 映射后的X坐标（输出）
 * @param my 映射后的Y坐标（输出）
 * 
 * @note 此函数根据当前屏幕方向，将输入的坐标映射到实际的屏幕坐标。
 */
static int8_t LCD_MapCoords(uint16_t x, uint16_t y, uint16_t *mx, uint16_t *my) {
    switch (lcd_orientation) {
        case LCD_ORIENTATION_PORTRAIT: // 0°
            *mx = x;
            *my = y;
            break;
        case LCD_ORIENTATION_LANDSCAPE: // 90°顺时针
            *mx = y;
            *my = LCD_HEIGHT - 1 - x;
            break;
        case LCD_ORIENTATION_LANDSCAPE_INVERTED: // 90°逆时针
            *mx = LCD_WIDTH - 1 - y;
            *my = x;
            break;
        case LCD_ORIENTATION_PORTRAIT_INVERTED: // 180°
            *mx = LCD_WIDTH - 1 - x;
            *my = LCD_HEIGHT - 1 - y;
            break;
        default:
            *mx = x;
            *my = y;
            break;
    }
    return DEVICE_OK;
}

/**
 * 设置LCD绘图窗口
 * 
 * @param x 窗口起始X坐标
 * @param y 窗口起始Y坐标
 * @param w 窗口宽度
 * @param h 窗口高度
 * 
 * @note 此函数用于设置LCD的绘图窗口，指定后续绘图操作的区域。
 */
static int8_t LCD_SetAddressWindow(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    uint16_t x_start = x + X_OFFSET; // 计算窗口起始X坐标
    uint16_t x_end = x_start + w - 1; // 计算窗口结束X坐标
    uint16_t y_start = y + Y_OFFSET; // 计算窗口起始Y坐标
    uint16_t y_end = y_start + h - 1; // 计算窗口结束Y坐标

    LCD_WriteCommand(0x2A); // 列地址设置
    uint8_t data_x[] = {x_start >> 8, x_start & 0xFF, x_end >> 8, x_end & 0xFF};
    LCD_WriteDataBuffer(data_x, sizeof(data_x));

    LCD_WriteCommand(0x2B); // 行地址设置
    uint8_t data_y[] = {y_start >> 8, y_start & 0xFF, y_end >> 8, y_end & 0xFF};
    LCD_WriteDataBuffer(data_y, sizeof(data_y));

    LCD_WriteCommand(0x2C); // 内存写入

    return DEVICE_OK;
}
/* Exported functions ------------------------------------------------------- */

/**
 * 初始化LCD
 * 
 * @param orientation 屏幕方向（竖屏、横屏等）
 * 
 * @note 此函数用于初始化LCD显示屏，设置屏幕方向、像素格式、伽马校正等参数。
 *       根据传入的屏幕方向参数，调整屏幕的显示方向。
 */
int8_t LCD_Init(LCD_Orientation_t orientation) {
    lcd_orientation = orientation; // 设置屏幕方向

    LCD_RST_LOW(); // 复位引脚低电平
    HAL_Delay(50); // 延时
    LCD_RST_HIGH(); // 复位引脚高电平
    HAL_Delay(50); // 延时

    LCD_WriteCommand(0x36); // 内存数据访问控制
    switch (orientation) {
        case LCD_ORIENTATION_PORTRAIT: // 竖屏模式
            LCD_WriteData(0x08); // MY=1, MX=0, MV=0, ML=0, BGR=0
            break;
        case LCD_ORIENTATION_LANDSCAPE: // 横屏模式（90°顺时针旋转）
            LCD_WriteData(0x60); // MY=0, MX=1, MV=1, ML=0, BGR=0
            break;
        case LCD_ORIENTATION_LANDSCAPE_INVERTED: // 横屏模式（90°逆时针旋转）
            LCD_WriteData(0xA0); // MY=1, MX=1, MV=1, ML=0, BGR=0
            break;
        case LCD_ORIENTATION_PORTRAIT_INVERTED: // 竖屏模式（180°旋转）
            LCD_WriteData(0xC8); // MY=1, MX=1, MV=0, ML=0, BGR=0
            break;
        default:
            // LCD_WriteData(0x08); // 默认竖屏模式
            break;
    }

    LCD_WriteCommand(0x3A); // 接口像素格式
    LCD_WriteData(0x05);    // 16位色

    LCD_WriteCommand(0xB2); // 前廊设置
    uint8_t porch[] = {0x0C, 0x0C, 0x00, 0x33, 0x33};
    LCD_WriteDataBuffer(porch, sizeof(porch));

    LCD_WriteCommand(0xB7); // 门控设置
    LCD_WriteData(0x35);

    LCD_WriteCommand(0xBB); // VCOM设置
    LCD_WriteData(0x19);

    LCD_WriteCommand(0xC0); // LCM控制
    LCD_WriteData(0x2C);

    LCD_WriteCommand(0xC2); // VDV和VRH命令使能
    LCD_WriteData(0x01);

    LCD_WriteCommand(0xC3); // VRH设置
    LCD_WriteData(0x12);

    LCD_WriteCommand(0xC4); // VDV设置
    LCD_WriteData(0x20);

    LCD_WriteCommand(0xC6); // 帧率控制
    LCD_WriteData(0x0F);

    LCD_WriteCommand(0xD0); // 电源控制1
    LCD_WriteData(0xA4);
    LCD_WriteData(0xA1);

    LCD_WriteCommand(0xE0); // 正电压伽马控制
    uint8_t gamma_pos[] = {0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23};
    LCD_WriteDataBuffer(gamma_pos, sizeof(gamma_pos));

    LCD_WriteCommand(0xE1); // 负电压伽马控制
    uint8_t gamma_neg[] = {0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23};
    LCD_WriteDataBuffer(gamma_neg, sizeof(gamma_neg));

    LCD_WriteCommand(0x21); // 显示反转开启
    LCD_WriteCommand(0x11); // 退出睡眠模式
    HAL_Delay(120); // 延时
    LCD_WriteCommand(0x29); // 显示开启

    return DEVICE_OK;
}

/**
 * 清屏函数
 * 
 * @param color 清屏颜色（RGB565格式）
 * 
 * @note 此函数用于将整个LCD屏幕填充为指定颜色。
 */
int8_t LCD_Clear(uint16_t color) {
    uint8_t color_data[] = {color >> 8, color & 0xFF}; // 将颜色转换为字节数组
    LCD_SetAddressWindow(0, 0, LCD_WIDTH, LCD_HEIGHT); // 设置整个屏幕为绘制窗口

    // 创建一个缓冲区，用于存储一行的颜色数据
    uint32_t row_size = LCD_WIDTH * 2; // 每行像素占用 2 字节
    uint8_t *row_buffer = (uint8_t *)malloc(row_size);
    if (row_buffer == NULL) return DEVICE_ERR_NULL; // 分配失败，直接返回

    // 填充缓冲区为目标颜色
    for (uint32_t i = 0; i < row_size; i += 2) {
        row_buffer[i] = color_data[0];
        row_buffer[i + 1] = color_data[1];
    }

    // 按行传输数据，覆盖整个屏幕
    for (uint32_t y = 0; y < LCD_HEIGHT; y++) {
        LCD_WriteDataBuffer_DMA(row_buffer, row_size);
    }

    free(row_buffer); // 释放缓冲区

    return DEVICE_OK;
}

/**
 * 绘制单个像素点
 * 
 * @param x X坐标
 * @param y Y坐标
 * @param color 像素颜色（RGB565格式）
 * 
 * @note 此函数用于在指定位置绘制一个像素点。
 */
int8_t LCD_DrawPoint(uint16_t x, uint16_t y, uint16_t color) {
    uint16_t mx, my;
    LCD_MapCoords(x, y, &mx, &my); // 根据屏幕方向映射坐标
    LCD_SetAddressWindow(mx, my, 1, 1); // 设置绘制窗口为单个像素
    uint8_t color_data[] = { (uint8_t)(color >> 8), (uint8_t)(color & 0xFF) }; // 将颜色转换为字节数组
    LCD_WriteDataBuffer(color_data, 2); // 写入像素数据

    return DEVICE_OK;
}

/**
 * 绘制直线
 * 
 * @param x0 起始X坐标
 * @param y0 起始Y坐标
 * @param x1 终止X坐标
 * @param y1 终止Y坐标
 * @param color 直线颜色（RGB565格式）
 * 
 * @note 此函数使用Bresenham算法绘制直线。
 */
int8_t LCD_DrawLine(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1, uint16_t color) {
    int dx = x1 - x0; // 计算X方向增量
    int dy = y1 - y0; // 计算Y方向增量
    int sx = (dx >= 0) ? 1 : -1; // X方向步长
    int sy = (dy >= 0) ? 1 : -1; // Y方向步长
    dx = dx >= 0 ? dx : -dx; // 取绝对值
    dy = dy >= 0 ? dy : -dy; // 取绝对值

    if (dx == 0 && dy == 0) { // 单点
        LCD_DrawPoint((uint16_t)x0, (uint16_t)y0, color);
        return DEVICE_OK;
    }

    if (dx > dy) { // X方向增量大于Y方向增量
        int err = dx / 2; // 初始化误差
        int x = x0;
        int y = y0;
        for (int i = 0; i <= dx; i++) {
            LCD_DrawPoint((uint16_t)x, (uint16_t)y, color); // 绘制当前点
            x += sx; // 更新X坐标
            err -= dy; // 更新误差
            if (err < 0) {
                y += sy; // 更新Y坐标
                err += dx; // 更新误差
            }
        }
    } else { // Y方向增量大于X方向增量
        int err = dy / 2; // 初始化误差
        int x = x0;
        int y = y0;
        for (int i = 0; i <= dy; i++) {
            LCD_DrawPoint((uint16_t)x, (uint16_t)y, color); // 绘制当前点
            y += sy; // 更新Y坐标
            err -= dx; // 更新误差
            if (err < 0) {
                x += sx; // 更新X坐标
                err += dy; // 更新误差
            }
        }
    }
    return DEVICE_OK;
}

/**
 * 绘制矩形
 * 
 * @param x1 矩形左上角X坐标
 * @param y1 矩形左上角Y坐标
 * @param x2 矩形右下角X坐标
 * @param y2 矩形右下角Y坐标
 * @param color 矩形颜色（RGB565格式）
 * 
 * @note 此函数通过绘制四条边来绘制矩形。
 */
int8_t LCD_DrawRectangle(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, uint16_t color) {
    LCD_DrawLine(x1, y1, x2, y1, color); // 上边
    LCD_DrawLine(x1, y1, x1, y2, color); // 左边
    LCD_DrawLine(x1, y2, x2, y2, color); // 下边
    LCD_DrawLine(x2, y1, x2, y2, color); // 右边
    return DEVICE_OK;
}

int8_t LCD_DrawSolidRectangle(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, uint16_t color) {
    int8_t a;
	if(y1>y2) a=1;
	else a=-1;
	while(y1!=y2) {
	LCD_DrawLine(x1, y1, x2, y1, color); // 上边
    LCD_DrawLine(x1, y2, x2, y2, color); // 下边
	y1-=a;y2+=a;
	}
    return DEVICE_OK;
}
/**
 * 绘制空心圆
 * 
 * @param x0 圆心X坐标
 * @param y0 圆心Y坐标
 * @param r 圆的半径
 * @param color 圆的颜色（RGB565格式）
 * 
 * @note 此函数使用中点圆算法绘制空心圆。
 */
int8_t LCD_DrawHollowCircle(uint16_t x0, uint16_t y0, uint16_t r, uint16_t color) {
    int a = 0; // X方向增量
    int b = r; // Y方向增量

    while (a <= b) {
        LCD_DrawPoint(x0 - b, y0 - a, color); // 第3象限
        LCD_DrawPoint(x0 + b, y0 - a, color); // 第0象限
        LCD_DrawPoint(x0 - a, y0 + b, color); // 第1象限
        LCD_DrawPoint(x0 - a, y0 - b, color); // 第2象限
        LCD_DrawPoint(x0 + b, y0 + a, color); // 第4象限
        LCD_DrawPoint(x0 + a, y0 - b, color); // 第5象限
        LCD_DrawPoint(x0 + a, y0 + b, color); // 第6象限
        LCD_DrawPoint(x0 - b, y0 + a, color); // 第7象限

        a++; // 更新X方向增量
        if ((a * a + b * b) > (r * r)) { // 判断是否超出半径范围
            b--; // 更新Y方向增量
        }
    }
    return DEVICE_OK;
}

/**
 * 绘制实心圆
 * 
 * @param x0 圆心X坐标
 * @param y0 圆心Y坐标
 * @param r 圆的半径
 * @param color 圆的颜色（RGB565格式）
 * 
 * @note 此函数使用中点圆算法绘制实心圆，通过填充水平线段实现。
 */
int8_t LCD_DrawSolidCircle(uint16_t x0, uint16_t y0, uint16_t r, uint16_t color) {
    int a = 0; // X方向增量
    int b = r; // Y方向增量
    int r2 = r * r; // 预计算半径的平方

    while (a <= b) {
        // 绘制8个对称点并填充水平线段
        LCD_DrawLine(x0 - b, y0 - a, x0 + b, y0 - a, color); // 第3象限
        LCD_DrawLine(x0 - b, y0 + a, x0 + b, y0 + a, color); // 第4象限
        LCD_DrawLine(x0 - a, y0 - b, x0 + a, y0 - b, color); // 第2象限
        LCD_DrawLine(x0 - a, y0 + b, x0 + a, y0 + b, color); // 第6象限

        a++; // 更新X方向增量
        if ((a * a + b * b) > r2) { // 判断是否超出半径范围
            b--; // 更新Y方向增量
        }
    }
    return DEVICE_OK;
}

/**
 * 绘制字符
 * 
 * @param x 字符起始X坐标
 * @param y 字符起始Y坐标
 * @param ch 要绘制的字符
 * @param color 字符颜色（RGB565格式）
 * @param font_size 字体大小（12或32）
 * @param bit_order 位顺序（LSB或MSB）
 * 
 * @note 此函数根据字体大小和位顺序绘制单个字符。
 */
int8_t LCD_DrawChar(uint16_t x, uint16_t y, char ch, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order) {
    if (ch < ' ' || ch > '~') { // 检查字符是否在可打印范围内
        return DEVICE_ERR;
    }

    uint8_t index = ch - ' '; // 计算字符索引

    const uint8_t *font_data=NULL;
    uint8_t char_width=0;
    uint8_t char_height=0;
    uint8_t bytesPerRow=0;

    switch (font_size) {
        case 12:// 12x6 字体（ascii_1206，特殊位映射 bit5..bit0）
            #ifdef ASCII_1206
            font_data = (const uint8_t *)ascii_1206[index];
            char_width = 6;
            char_height = 12;

            for (uint8_t row = 0; row < char_height; row++) {
                for (uint8_t col = 0; col < char_width; col++) {
                    uint16_t pixel_x = x + col;
                    uint16_t pixel_y = y + row;
                    uint8_t bit_value;
                    if (bit_order == MSB) { // MSB 优先，项目约定：6 位放在 bit5..bit0
                        bit_value = (font_data[row] >> (5 - col)) & 0x01;
                    } else { // LSB 优先
                        bit_value = (font_data[row] >> col) & 0x01;
                    }
                    if (bit_value) {
                        LCD_DrawPoint(pixel_x, pixel_y, color);
                    }
                }
            }
            #endif
            break;
        case 16:// 16x8 字体（ascii_1608：按行存储，每行 1 字节，MSB-first 常规映射）
            #ifdef ASCII_1608
            font_data = (const uint8_t *)ascii_1608[index];
            char_width = 8;
            char_height = 16;

            for (uint8_t row = 0; row < char_height; row++) {
                uint8_t row_byte = font_data[row];
                for (uint8_t col = 0; col < char_width; col++) {
                    uint16_t pixel_x = x + col;
                    uint16_t pixel_y = y + row;
                    uint8_t bit_value;
                    if (bit_order == MSB) {
                        bit_value = (row_byte >> (7 - col)) & 0x01; // MSB-first: bit7 -> col0
                    } else {
                        bit_value = (row_byte >> col) & 0x01;       // LSB-first
                    }
                    if (bit_value) {
                        LCD_DrawPoint(pixel_x, pixel_y, color);
                    }
                }
            }
            #endif
            break;
        case 24:// 24x12 字体（ascii_2412：按行存储，每行 2 字节）
            #ifdef ASCII_2412
            font_data = (const uint8_t *)ascii_2412[index];
            char_width = 12;
            char_height = 24;
            bytesPerRow = (char_width + 7) / 8; // =2

            for (uint8_t row = 0; row < char_height; row++) {
                for (uint8_t col = 0; col < char_width; col++) {
                    uint16_t pixel_x = x + col;
                    uint16_t pixel_y = y + row;
                    uint8_t byte_index = col / 8;
                    uint8_t b = font_data[row * bytesPerRow + byte_index];
                    uint8_t bit_value;
                    if (bit_order == MSB) {
                        bit_value = (b >> (7 - (col % 8))) & 0x01;
                    } else {
                        bit_value = (b >> (col % 8)) & 0x01;
                    }
                    if (bit_value) {
                        LCD_DrawPoint(pixel_x, pixel_y, color);
                    }
                }
            }
            #endif
            break;
        case 32:// 32x16 字体（ascii_3216：按行存储，每行 2 字节）
            #ifdef ASCII_3216
            font_data = (const uint8_t *)ascii_3216[index];
            char_width = 16;
            char_height = 32;
            bytesPerRow = (char_width + 7) / 8; // =2

            for (uint8_t row = 0; row < char_height; row++) {
                for (uint8_t col = 0; col < char_width; col++) {
                    uint16_t pixel_x = x + col;
                    uint16_t pixel_y = y + row;
                    uint8_t byte_index = col / 8;
                    uint8_t b = font_data[row * bytesPerRow + byte_index];
                    uint8_t bit_value;
                    if (bit_order == MSB) {
                        bit_value = (b >> (7 - (col % 8))) & 0x01;
                    } else {
                        bit_value = (b >> (col % 8)) & 0x01;
                    }
                    if (bit_value) {
                        LCD_DrawPoint(pixel_x, pixel_y, color);
                    }
                }
            }
            #endif
            break;
        default:
            return DEVICE_ERR;
    }

    return DEVICE_OK;
}

/**
 * 绘制字符串
 * 
 * @param x 字符串起始X坐标
 * @param y 字符串起始Y坐标
 * @param str 要绘制的字符串
 * @param color 字符颜色（RGB565格式）
 * @param font_size 字体大小（12或32）
 * @param bit_order 位顺序（LSB或MSB）
 * 
 * @note 此函数逐字符绘制字符串，支持换行。
 */
int8_t LCD_DrawString(uint16_t x, uint16_t y, const char *str, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order) {
    uint16_t cursor_x = x;
    uint16_t cursor_y = y;
    uint8_t char_width, char_height, x_spacing, y_spacing;

    switch (font_size) {
        case 12:
            #ifdef ASCII_1206
            char_width = 6;
            char_height = 12;
            x_spacing = 7;      // 推荐间距：宽度+1
            y_spacing = 13;     // 行间距：高度+1
            #endif
            break;
        case 16:
            #ifdef ASCII_1608
            char_width = 8;
            char_height = 16;
            x_spacing = 9;  
            y_spacing = 17; 
            #endif
            break;
        case 24:
            #ifdef ASCII_2412
            char_width = 12;
            char_height = 24;
            x_spacing = 13;
            y_spacing = 25;
            #endif
            break;
        case 32:
            #ifdef ASCII_3216
            char_width = 16;
            char_height = 32;
            x_spacing = 17;
            y_spacing = 33;
            #endif
            break;
        default:
            return DEVICE_ERR;// 不支持的字体大小
    }

    while (*str) {
        if (*str == '\n') {
            cursor_x = x;
            cursor_y += y_spacing;
            str++;
            continue;
        }

        LCD_DrawChar(cursor_x, cursor_y, *str, color, font_size, bit_order);
        cursor_x += x_spacing;
        str++;
    }
}

/**
 * 绘制整数
 * 
 * @param x 起始X坐标
 * @param y 起始Y坐标
 * @param num 要绘制的整数
 * @param color 数字颜色（RGB565格式）
 * @param font_size 字体大小（12或32）
 * @param bit_order 位顺序（LSB或MSB）
 * 
 * @note 此函数将整数转换为字符串后调用LCD_DrawString绘制。
 */
int8_t LCD_DrawInteger(uint16_t x, uint16_t y, int32_t num, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order) {
    char buffer[12]; // 缓冲区，足够存储32位整数的字符串表示
    snprintf(buffer, sizeof(buffer), "%d", num); // 将整数转换为字符串
    LCD_DrawString(x, y, buffer, color, font_size, bit_order); // 调用字符串绘制函数
    return DEVICE_OK;
}

/**
 * 绘制浮点数
 * 
 * @param x 起始X坐标
 * @param y 起始Y坐标
 * @param num 要绘制的浮点数
 * @param decimal_places 小数点后保留的位数
 * @param color 数字颜色（RGB565格式）
 * @param font_size 字体大小（12或32）
 * @param bit_order 位顺序（LSB或MSB）
 * 
 * @note 此函数将浮点数转换为字符串后调用LCD_DrawString绘制。
 */
int8_t LCD_DrawFloat(uint16_t x, uint16_t y, float num, uint8_t decimal_places, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order) {
    char buffer[20]; // 缓冲区，足够存储浮点数的字符串表示
    snprintf(buffer, sizeof(buffer), "%.*f", decimal_places, num); // 将浮点数转换为字符串
    LCD_DrawString(x, y, buffer, color, font_size, bit_order); // 调用字符串绘制函数
    return DEVICE_OK;
}

/**
 * 绘制位图
 * 
 * @param bitmap 位图数据指针
 * @param x 位图起始X坐标
 * @param y 位图起始Y坐标
 * @param width 位图宽度（像素）
 * @param height 位图高度（像素）
 * @param color 绘制颜色（RGB565格式）
 * 
 * @note 此函数逐像素绘制位图，适用于简单的位图显示。如果需要更高性能，可以优化为按行发送。
 */
int8_t LCD_DrawBitmap(const uint8_t *bitmap, uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color, LCD_BitOrder_t bit_order) {
    if (bitmap == NULL) return DEVICE_ERR_NULL; // 检查位图指针是否为空
    uint16_t bytesPerRow = (width + 7) / 8; // 每行的字节数

    for (uint16_t row = 0; row < height; row++) { // 遍历每一行
        const uint8_t *row_ptr = bitmap + (uint32_t)row * bytesPerRow; // 当前行的起始指针
        for (uint16_t byte_i = 0; byte_i < bytesPerRow; byte_i++) { // 遍历每一行的字节
            uint8_t b = row_ptr[byte_i]; // 当前字节
            for (uint8_t bit = 0; bit < 8; bit++) { // 遍历每个字节的位
                uint16_t col = (uint16_t)byte_i * 8 + bit; // 计算当前像素的列坐标
                if (col >= width) break; // 如果超出宽度范围，跳过

                uint8_t pixel_on = 0;
                if (bit_order == MSB) {
                    // MSB-first：字节内最高位(0x80)对应当前字节块的最左像素
                    pixel_on = (b & (0x80 >> bit)) ? 1 : 0;
                } else {
                    // LSB-first：字节内最低位(0x01)对应当前字节块的最左像素
                    pixel_on = (b & (1U << bit)) ? 1 : 0;
                }

                if (pixel_on) { // 如果当前位为1，则绘制像素
                    LCD_DrawPoint((uint16_t)(x + col), (uint16_t)(y + row), color);
                }
            }
        }
    }
    return DEVICE_OK;
}