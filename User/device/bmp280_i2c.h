#pragma once

/*底层接口定义*/
#include "bsp/i2c.h"
#include "stdint.h"

#define BMP280_I2C_ADDR 0x76  // BMP280 默认 I2C 地址

/*寄存器地址*/
#define BMP280_ID 0xD0      // 设备ID地址
#define BMP280_RESET 0xE0   // 设备重启
#define BMP280_STATUS 0xF3  // 设备状态
#define BMP280_CTRL_MEAS 0xF4  // 数据采集和模式设置
#define BMP280_CONFIG 0xF5  // 采样速率，滤波器和接口设置
#define BMP280_DIGT 0x88  // 温度校准系数起始位置
#define BMP280_DIGP 0x8E  // 气压校准系数起始位置
#define BMP280_TEMP 0xFA  // 温度储存起始位置
#define BMP280_PRES 0xF7  // 气压储存起始位置

#define BMP2_CHIP_ID 0x58  // 设备ID地址

#define bmp280_msblsb_to_u16(msb, lsb) (((uint16_t)msb << 8) | ((uint16_t)lsb))

typedef struct {
    unsigned short dig_t1;
    signed short dig_t2;
    signed short dig_t3;
    unsigned short dig_p1;
    signed short dig_p2;
    signed short dig_p3;
    signed short dig_p4;
    signed short dig_p5;
    signed short dig_p6;
    signed short dig_p7;
    signed short dig_p8;
    signed short dig_p9;
} bmp280_calib;

uint8_t bmp280_get_id(void);
uint8_t bmp280_reset(void);
uint8_t bmp280_getStatus(void);
uint8_t bmp280_setMode(uint8_t mode);
uint8_t bmp280_setOversampling(uint8_t osrs_p, uint8_t osrs_t);
uint8_t bmp280_setConfig(uint8_t Standbyt, uint8_t filter);
void bmp280_getCalibration(bmp280_calib *calib);
void bmp280_getTemperature(bmp280_calib *calib, double *temperature, int32_t *t_fine);
void bmp280_getPressure(bmp280_calib *calib, double *pressure, int32_t *t_fine);
uint8_t bmp280_init(bmp280_calib *calib);
void bmp280_getdata(bmp280_calib *calib, float *temperature, float *pressure);
