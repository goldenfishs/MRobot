#include "bmp280_i2c.h"
#include "bsp/i2c.h"

#define I2C_Handle BSP_I2C_GetHandle(BSP_I2C_BMP280)

/**
 * @brief  读寄存器
 * @param  regAdd 寄存器开始地址
 * @param  pdata  存储数据的指针
 * @param  size   寄存器个数
 * @retval 无
 */
void bmp280_readReg(uint8_t regAdd, uint8_t *pdata, uint8_t size) {
    HAL_I2C_Mem_Read(I2C_Handle, BMP280_I2C_ADDR << 1, regAdd, I2C_MEMADD_SIZE_8BIT, pdata, size, 1000);
}



/**
 * @brief  写1个寄存器
 * @param  regAdd 寄存器开始地址
 * @param  pdata  存储数据的指针
 * @retval 0 写入成功
 *         1 写入失败
 */
uint8_t bmp280_writeReg(uint8_t regAdd, uint8_t *pdata) {
    if (HAL_I2C_Mem_Write(I2C_Handle, BMP280_I2C_ADDR << 1, regAdd, I2C_MEMADD_SIZE_8BIT, pdata, 1, 1000) == HAL_OK) {
        return 0;
    }
    return 1;
}


/**
 * @brief  读取设备物理id，用于调试
 * @param  无
 * @retval 设备id
 */
uint8_t bmp280_get_id(void) {
    uint8_t temp = 0;
    bmp280_readReg(BMP280_ID, &temp, 1);
    return temp;
}

/**
 * @brief  重启设备
 * @param  无
 * @retval 0 重启成功
 *         1 重启失败
 */
uint8_t bmp280_reset(void) {
    uint8_t temp = 0xB6;
    return bmp280_writeReg(BMP280_RESET, &temp);
}

/**
 * @brief  获取设备状态
 * @param  无
 * @retval 0 空闲
 *         1 正在测量或者正在复制
 */
uint8_t bmp280_getStatus(void) {
    uint8_t temp = 0;
    bmp280_readReg(BMP280_STATUS, &temp, 1);
    return (temp & 0x09) ? 1 : 0;
}


 /**
  * @brief  工作模式设置推荐
  * @param 	mode 0 睡眠模式
  *              1 单次测量模式，测量完成后回到休眠模式
  *              2 连续测量模式
  * @retval 0 设置成功
  *         1 设置失败 
  */
uint8_t bmp280_setMode(uint8_t mode)
{
	uint8_t temp=0;
	bmp280_readReg(BMP280_CTRL_MEAS,&temp,1);
	switch(mode)
	{
		case 0: 
			temp&=0xFC;
			break;
		case 1:
			temp&=0xFC;
			temp|=0x01;
			break;
		case 2:
			temp&=0xFC;
			temp|=0x03;	
			break;
		default: 
			return 1;
	}
	return bmp280_writeReg(BMP280_CTRL_MEAS,&temp);
}


 /**
  * @brief  过采样设置
  * @param 	mode temp&press 0 禁用
  *                  1 过采样×1
  *                  2 过采样×2
  *                  3 过采样×4
  *                  ..  .....
  *                  5 过采样×16
  * @retval 0 设置成功
  *         1 设置失败 
  */
uint8_t bmp280_setOversampling(uint8_t osrs_p,uint8_t osrs_t)
{
	uint8_t temp=0;
	bmp280_readReg(BMP280_CTRL_MEAS,&temp,1);
	temp&=0xE3;
	osrs_p = osrs_p<<2;
	osrs_p&= 0x1C;
	temp|=osrs_p;
	
	temp&=0x1F;
	osrs_t = osrs_t<<5;
	osrs_t&= 0xE0;
	temp|=osrs_t;
	return bmp280_writeReg(BMP280_CTRL_MEAS,&temp);
}


 /**
  * @brief  滤波器系数和采样间隔时间设置
  * @param 	Standbyt   0 0.5ms    filter  0 关闭滤波器
  *                  1 62.5ms           1 2
  *                  2 125ms            2 4
  *                  3 250ms            3 8
  *                  4 500ms            4 16
  *                  5 1000ms
  *                  6 2000ms
  *                  7 4000ms
  * @retval 0 设置成功
  *         1 设置失败 
  */
uint8_t bmp280_setConfig(uint8_t Standbyt,uint8_t filter)
{
		uint8_t temp=0;
		temp = Standbyt<<5;
		filter&=0x07;
		filter=filter<<2;
		temp|=filter;
		return bmp280_writeReg(BMP280_CONFIG,&temp);
}


 /**
  * @brief  获取校准系数
  * @param 	calib 储存系数的结构体
  * @retval 无
  */
void bmp280_getCalibration(bmp280_calib *calib)
{
	uint8_t buf[20];
	bmp280_readReg(BMP280_DIGT,buf,6);
	calib->dig_t1 =(uint16_t)(bmp280_msblsb_to_u16(buf[1], buf[0])); 
	calib->dig_t2 =(int16_t)(bmp280_msblsb_to_u16(buf[3], buf[2])); 
	calib->dig_t3 =(int16_t)(bmp280_msblsb_to_u16(buf[5], buf[4])); 
	bmp280_readReg(BMP280_DIGP,buf,18);
	calib->dig_p1 = (uint16_t)(bmp280_msblsb_to_u16(buf[1], buf[0])); 
	calib->dig_p2 =(int16_t)(bmp280_msblsb_to_u16(buf[3], buf[2]));
  calib->dig_p3 =(int16_t)(bmp280_msblsb_to_u16(buf[5], buf[4])); 
  calib->dig_p4 =(int16_t)(bmp280_msblsb_to_u16(buf[7], buf[6])); 
  calib->dig_p5 =(int16_t)(bmp280_msblsb_to_u16(buf[9], buf[8])); 
  calib->dig_p6 =(int16_t)(bmp280_msblsb_to_u16(buf[11], buf[10])); 
  calib->dig_p7 =(int16_t)(bmp280_msblsb_to_u16(buf[13], buf[12])); 
  calib->dig_p8 =(int16_t)(bmp280_msblsb_to_u16(buf[15], buf[14])); 
  calib->dig_p9 =(int16_t)(bmp280_msblsb_to_u16(buf[17], buf[16])); 	
}



 /**
  * @brief  获取温度
  * @param 	calib 系数的结构体
  *       *temperature 温度值指针
  *       *t_fine  精细分辨率温度值指针
  * @retval 无 
  */
void bmp280_getTemperature(bmp280_calib *calib,double *temperature,int32_t *t_fine)
{
	uint8_t buf[3];
	uint32_t data_xlsb;
  uint32_t data_lsb;
  uint32_t data_msb;
	int32_t uncomp_temperature;
	double var1, var2;

	bmp280_readReg(BMP280_TEMP,buf,3);
	data_msb = (int32_t)buf[0] << 12;
  data_lsb = (int32_t)buf[1] << 4;
  data_xlsb = (int32_t)buf[2] >> 4;
	uncomp_temperature = (int32_t)(data_msb | data_lsb | data_xlsb);


   var1 = (((double) uncomp_temperature) / 16384.0 - ((double) calib->dig_t1) / 1024.0) *
           ((double) calib->dig_t2);
   var2 =
        ((((double) uncomp_temperature) / 131072.0 - ((double) calib->dig_t1) / 8192.0) *
         (((double) uncomp_temperature) / 131072.0 - ((double) calib->dig_t1) / 8192.0)) *
        ((double) calib->dig_t3);
	*t_fine = (int32_t) (var1 + var2);
	 *temperature = (var1 + var2) / 5120.0;
}


 /**
  * @brief  获取气压
  * @param 	calib 系数的结构体
  *       *pressure 气压值指针
  *       *t_fine 精细分辨率温度值指针
  * @retval 无 
  */
void bmp280_getPressure(bmp280_calib *calib,double *pressure,int32_t *t_fine)
{
	uint8_t buf[3];
	uint32_t data_xlsb;
  uint32_t data_lsb;
  uint32_t data_msb;
	int32_t uncomp_pressure;
	double var1, var2;
	
	bmp280_readReg(BMP280_PRES,buf,3);
	data_msb = (uint32_t)buf[0] << 12;
  data_lsb = (uint32_t)buf[1] << 4;
  data_xlsb = (uint32_t)buf[2] >> 4;
	uncomp_pressure = (data_msb | data_lsb | data_xlsb);
	
	var1 = ((double) *t_fine / 2.0) - 64000.0;
  var2 = var1 * var1 * ((double) calib->dig_p6) / 32768.0;
  var2 = var2 + var1 * ((double) calib->dig_p5) * 2.0;
  var2 = (var2 / 4.0) + (((double) calib->dig_p4) * 65536.0);
  var1 = (((double)calib->dig_p3) * var1 * var1 / 524288.0 + ((double)calib->dig_p2) * var1) /
           524288.0;
  var1 = (1.0 + var1 / 32768.0) * ((double) calib->dig_p1);
	        *pressure = 1048576.0 - (double)uncomp_pressure;
        *pressure = (*pressure - (var2 / 4096.0)) * 6250.0 / var1;
        var1 = ((double)calib->dig_p9) * *pressure * *pressure / 2147483648.0;
        var2 = *pressure * ((double)calib->dig_p8) / 32768.0;

        *pressure = *pressure + (var1 + var2 + ((double)calib->dig_p7)) / 16.0;
}	


 /**
  * @brief  初始化
  * @param 	*calib 系数的结构体指针
  * @retval 0 设置成功
  *         1 设置失败
  */
uint8_t bmp280_init(bmp280_calib *calib)
{
		uint8_t rslt;
		rslt = bmp280_get_id();
		if(rslt == BMP2_CHIP_ID)
		{
			bmp280_getCalibration(calib);
			rslt = bmp280_setOversampling(5,2);
			if(rslt)
			{
				return 1;
			}
			rslt = bmp280_setConfig(0,4);
			if(rslt)
			{
				return 1;
			}
			rslt = bmp280_setMode(2);
			if(rslt)
			{
				return 1;
			}
		}
		else
		{
			return 1;	
		}
		return 0;
}


 /**
  * @brief  获取最终数据
  * @param 	*calib 系数的结构体指针
  * @retval 无 
  */
void bmp280_getdata(bmp280_calib *calib,float *temperature,float *pressure)
{	
		double temp_T,temp_P;
		int32_t t_fine; 
		bmp280_getTemperature(calib,&temp_T,&t_fine);
		bmp280_getPressure(calib,&temp_P,&t_fine);
		*temperature = (float)temp_T;
		*pressure = (float)temp_P;
}	
