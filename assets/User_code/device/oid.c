/* 
    oid编码器驱动 
*/

/*编码器can通信的默认波特率为500kHZ*/
/* Includes ----------------------------------------------------------------- */
#include "device/oid.h"
#include "bsp/time.h"
#include "mm.h"
/* Private function prototypes ---------------------------------------------- */

static OID_CANManager_t* OID_GetCANManager(BSP_CAN_t can);

/* Private functions -------------------------------------------------------- */

static OID_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/**
  * @brief         接收数据处理
  * @param[in]     none
  * @retval        none
  */
static void OID_ParseFeedbackFrame( OID_t *encoder , uint8_t *rx_data )
{
		if(encoder->param.id == rx_data[1])//判断编码器id
		{
				switch(rx_data[2])//判断指令
				{ 
					case 0x01:
						encoder->feedback.angle_fbk = rx_data[3]|rx_data[4]<<8|rx_data[5]<<16|rx_data[6]<<24;
						encoder->feedback.angle_360 = encoder->feedback.angle_fbk*360.0f/OID_RESOLUTION;
						encoder->feedback.angle_2PI = encoder->feedback.angle_fbk*M_2PI/OID_RESOLUTION;
						break;
				
					case 0x0A:
						encoder->feedback.speed_fbk=rx_data[3]|rx_data[4]<<8|rx_data[5]<<16|rx_data[6]<<24;
						encoder->feedback.speed_rpm=encoder->feedback.speed_fbk/OID_RESOLUTION/(0.1f/60.0f);
						break;
					
					default:
						 break;
				}
		}
}

int8_t OID_Update(OID_Param_t *param)
{
	
		if (param == NULL) return DEVICE_ERR_NULL;
		
    OID_CANManager_t *manager = OID_GetCANManager(param->can);
		if (manager == NULL) return DEVICE_ERR_NULL;
		
		OID_t *encoder = NULL;
 
		for (int i = 0; i < manager->encoder_count; i++) {
        if (manager->encoders[i] && manager->encoders[i]->param.id == param->id) {
            encoder = manager->encoders[i];
            break;
        }
    }
		
		 if (encoder == NULL) return DEVICE_ERR_NO_DEV;
		
    // 从CAN队列获取数据
		BSP_CAN_Message_t rx_msg;
    if (BSP_CAN_GetMessage( param->can , param->id , &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) 
		{
        uint64_t now_time = BSP_TIME_Get();
        if (now_time - encoder->header.last_online_time > 100000) // 100ms超时，单位微秒
				{
            encoder->header.online = false;
				}
        return DEVICE_ERR;
    }
		
		encoder->header.online = true;
    encoder->header.last_online_time = BSP_TIME_Get();
		// 处理接收到的数据
    OID_ParseFeedbackFrame( encoder , rx_msg.data );
    return DEVICE_OK;  // 没有新数据
}

/**
 * @brief 更新所有编码器数据
 * @return 更新结果
 */
int8_t OID_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        OID_CANManager_t *manager = OID_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        
        for (int i = 0; i < manager->encoder_count; i++) {
            OID_t *encoder = manager->encoders[i];
            if (encoder != NULL) {
                if (OID_Update(&encoder->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

/**
 * @brief 获取指定CAN总线的管理器
 * @param can CAN总线
 * @return CAN管理器指针
 */
static OID_CANManager_t* OID_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) {
        return NULL;
    }
    
    return can_managers[can];
}

/**
 * @brief 创建CAN管理器
 * @param can CAN总线
 * @return 创建结果
 */
static int8_t OID_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    
    can_managers[can] = (OID_CANManager_t*)BSP_Malloc(sizeof(OID_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    
    memset(can_managers[can], 0, sizeof(OID_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

/**
 * @brief 注册一个欧艾迪编码器
 * @param param 编码器参数
 * @return 注册结果
 */
int8_t OID_Register(OID_Param_t *param)
{
		if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    /* 创建CAN管理器 */
    if (OID_CreateCANManager(param->can) != DEVICE_OK) {
        return DEVICE_ERR;
    }
    
    /* 获取CAN管理器 */
    OID_CANManager_t *manager = OID_GetCANManager(param->can);
    if (manager == NULL) {
        return DEVICE_ERR;
    }
    
    /* 检查是否已注册 */
    for (int i = 0; i < manager->encoder_count; i++) {
        if (manager->encoders[i] && manager->encoders[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    
    /* 检查是否已达到最大数量 */
    if (manager->encoder_count >= OID_MAX_NUM) {
        return DEVICE_ERR;
    }
    
    /* 分配内存 */
    OID_t *encoder = (OID_t *)BSP_Malloc(sizeof(OID_t));
    if (encoder == NULL) {
        return DEVICE_ERR;
    }
    
    /* 初始化电机 */
    memset(encoder, 0, sizeof(OID_t));
    memcpy(&encoder->param, param, sizeof(OID_Param_t));
    encoder->header.online = false;
//    encoder->encoder.reverse = param->reverse;
		
    /* 注册CAN接收ID - DM电机使用Master ID接收反馈 */
    uint16_t feedback_id = param->id;
    if (BSP_CAN_RegisterId(param->can, feedback_id, 3) != BSP_OK) {
        BSP_Free(encoder);
        return DEVICE_ERR;
    }

    /* 添加到管理器 */
    manager->encoders[manager->encoder_count] = encoder;
    manager->encoder_count++;
    
    return DEVICE_OK;
}

/**
 * @brief 使编码器离线（设置在线状态为false）
 * @param param 编码器参数
 * @return 操作结果
 */
int8_t OID_Offline(OID_Param_t *param) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    OID_t *encoder = OID_GetEncoder(param);
    if (encoder == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    encoder->header.online = false;
    return DEVICE_OK;
}

/**
 * @brief 获取指定编码器的实例指针
 * @param param 编码器参数
 * @return 编码器实例指针
 */
OID_t* OID_GetEncoder(OID_Param_t *param) {
    if (param == NULL) {
        return NULL;
    }
    
    OID_CANManager_t *manager = OID_GetCANManager(param->can);
    if (manager == NULL) {
        return NULL;
    }
    
    /* 查找对应的编码器 */
    for (int i = 0; i < manager->encoder_count; i++) {
        OID_t *encoder = manager->encoders[i];
        if (encoder && encoder->param.can == param->can && 
            encoder->param.id == param->id) {
            return encoder;
        }
    }
    
    return NULL;
}
/**
  * @brief         读取编码器值
  * @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Read_Value(OID_Param_t *param)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x01;
    frame.data[3] = 0x00;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器id
	* @param[in]     编码器当前id，编码器设置id
  * @retval        none
  */
int8_t  OID_Set_ID(OID_Param_t *param,OID_Param_t *param_new)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x02;
    frame.data[3] = param_new->id;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置can通讯波特率  0x00：500K（默认）；0x01:1M；0x02：250K；0x03:125K；0x04：100K；
	* @param[in]     编码器id，编码器设置波特率
  * @retval        none
  */
int8_t  OID_Set_Baudrate(OID_Param_t *param,OID_Baudrate_t encoder_vaud_rate)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x03;
    frame.data[3] = encoder_vaud_rate;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器模式  0x00：查询，0x02：自动返回编码器角速度值，0xAA：自动返回编码器值
	* @param[in]     编码器id，编码器设置模式
  * @retval        none
  */
int8_t  OID_Set_Mode(OID_Param_t *param,OID_Mode_t encoder_mode)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x04;
    frame.data[3] = encoder_mode;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器自动回传时间(掉电记忆，单位：微秒)，数值范围：50~65535（16 位无符号整数）
                   注意：设置太短的返回时间后，通过编码器上位机再设置其他参数很容易失败，谨慎使用！
	* @param[in]     编码器id，编码器自动回传时间
  * @retval        none
  */
int8_t  OID_Set_AutoFeedbackTime(OID_Param_t *param,uint8_t encoder_time)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x05;
    frame.data[3] = encoder_time;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置当前位置值为零点
	* @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Set_ZeroPoint(OID_Param_t *param)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x06;
    frame.data[3] = 0x00;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器值递增方向  0x00：顺时针，0x01：逆时针
	* @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Set_Polarity(OID_Param_t *param,OID_Direction_t encoder_direction)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x07;
    frame.data[3] = encoder_direction;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         读取编码器角度值
	* @param[in]     编码器id
  * @retval        none
	编码器旋转速度=编码器角速度值/单圈
	精度/转速计算时间（单位：转/分钟）
	例如：编码器角速度值回传为1000，单圈
	精度为32768，转速采样时间为
	100ms(0.1/60min)
	编码器旋转速度=1000/32768/(0.1/60)
	 =1000*0.0183=18.31转/分钟
  */
int8_t  OID_Read_AngularVelocity(OID_Param_t *param)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x0A;
    frame.data[3] = 0x00;

    
	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器角速度采样时间(掉电记忆，单位：毫秒)
	* @param[in]     编码器id,采样时间
  * @retval        none
  */
int8_t  OID_Set_AngularVelocitySamplingTime(OID_Param_t *param,uint8_t encoder_time)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x0B;
    frame.data[3] = encoder_time;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器中点   设定当前编码器值为 M(M 为单圈分辨率*圈数/2)
	* @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Set_Midpoint(OID_Param_t *param)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x0C;
    frame.data[3] = 0x01;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         设置编码器当前位置值  数值范围：0~X（X 为单圈分辨率*圈数- 1）
	* @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Set_CurrentPosition(OID_Param_t *param,uint8_t encoder_direction)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x0D;
    frame.data[3] = encoder_direction;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
/**
  * @brief         编码器设置当前值为 5 圈值   即当前编码器值为 Z(Z 为单圈分辨率*5)
	* @param[in]     编码器id
  * @retval        none
  */
int8_t  OID_Set_CurrentValue5Turns(OID_Param_t *param)
{
		BSP_CAN_StdDataFrame_t frame;
    frame.id = param->id;
    frame.dlc = 4;
		frame.data[0] = 0x04;
    frame.data[1] = param->id;
    frame.data[2] = 0x0F;
    frame.data[3] = 0x01;


	 return BSP_CAN_TransmitStdDataFrame(param->can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}


				 
