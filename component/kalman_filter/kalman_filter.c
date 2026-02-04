/*
  卡尔曼滤波器 modified from wang hongxi
  支持动态量测调整，使用ARM CMSIS DSP优化矩阵运算

  主要特性：
  - 基于量测有效性的 H、R、K 矩阵动态调整
  - 支持不同传感器采样频率
  - 矩阵 P 防过度收敛机制
  - ARM CMSIS DSP 优化的矩阵运算
  - 可扩展架构，支持用户自定义函数（EKF/UKF/ESKF）

  使用说明：
  1. 矩阵初始化：P、F、Q 使用标准初始化方式
     H、R 在使用自动调整时需要配置量测映射

  2. 自动调整模式 (use_auto_adjustment = 1)：
     - 提供 measurement_map：每个量测对应的状态索引
     - 提供 measurement_degree：H 矩阵元素值
     - 提供 mat_r_diagonal_elements：量测噪声方差

  3. 固定模式 (use_auto_adjustment = 0)：
     - 像初始化 P 矩阵那样正常初始化 z、H、R

  4. 量测更新：
     - 在传感器回调函数中更新 measured_vector
     - 值为 0 表示量测无效
     - 向量在每次 KF 更新后会被重置为 0

  5. 防过度收敛：
     - 设置 state_min_variance 防止 P 矩阵过度收敛
     - 帮助滤波器适应缓慢变化的状态

  使用示例：高度估计
  状态向量 x =
    |   高度      |
    |   速度      |
    |   加速度    |

  KF_t Height_KF;

  void INS_Task_Init(void)
  {
      // 初始协方差矩阵 P 
      static float P_Init[9] =
      {
          10, 0, 0,
          0, 30, 0,
          0, 0, 10,
      };

      // 状态转移矩阵 F（根据运动学模型）
      static float F_Init[9] =
      {
          1, dt, 0.5*dt*dt,
          0, 1, dt,
          0, 0, 1,
      };

      // 过程噪声协方差矩阵 Q
      static float Q_Init[9] =
      {
          0.25*dt*dt*dt*dt, 0.5*dt*dt*dt, 0.5*dt*dt,
          0.5*dt*dt*dt,        dt*dt,         dt,
          0.5*dt*dt,              dt,         1,
      };

      // 设置状态最小方差（防止过度收敛）
      static float state_min_variance[3] = {0.03, 0.005, 0.1};

      // 开启自动调整
      Height_KF.use_auto_adjustment = 1;

      // 量测映射：[气压高度对应状态1, GPS高度对应状态1, 加速度计对应状态3]
      static uint8_t measurement_reference[3] = {1, 1, 3};

      // 量测系数（H矩阵元素值）
      static float measurement_degree[3] = {1, 1, 1};
      // 根据 measurement_reference 与 measurement_degree 生成 H 矩阵如下
      // （在当前周期全部量测数据有效的情况下）
      //   |1   0   0|
      //   |1   0   0|
      //   |0   0   1|

      // 量测噪声方差（R矩阵对角元素）
      static float mat_r_diagonal_elements[3] = {30, 25, 35};
      // 根据 mat_r_diagonal_elements 生成 R 矩阵如下
      // （在当前周期全部量测数据有效的情况下）
      //   |30   0   0|
      //   | 0  25   0|
      //   | 0   0  35|

      // 初始化卡尔曼滤波器（状态维数3，控制维数0，量测维数3）
      KF_Init(&Height_KF, 3, 0, 3);

      // 设置矩阵初值
      memcpy(Height_KF.P_data, P_Init, sizeof(P_Init));
      memcpy(Height_KF.F_data, F_Init, sizeof(F_Init));
      memcpy(Height_KF.Q_data, Q_Init, sizeof(Q_Init));
      memcpy(Height_KF.measurement_map, measurement_reference,
             sizeof(measurement_reference));
      memcpy(Height_KF.measurement_degree, measurement_degree,
             sizeof(measurement_degree));
      memcpy(Height_KF.mat_r_diagonal_elements, mat_r_diagonal_elements,
             sizeof(mat_r_diagonal_elements));
      memcpy(Height_KF.state_min_variance, state_min_variance,
             sizeof(state_min_variance));
  }

  void INS_Task(void const *pvParameters)
  {
      // 循环更新卡尔曼滤波器
      KF_Update(&Height_KF);
      vTaskDelay(ts);
  }

  // 传感器回调函数示例：在数据就绪时更新 measured_vector
  void Barometer_Read_Over(void)
  {
      ......
      INS_KF.measured_vector[0] = baro_height;  // 气压计高度
  }

  void GPS_Read_Over(void)
  {
      ......
      INS_KF.measured_vector[1] = GPS_height;   // GPS高度
  }

  void Acc_Data_Process(void)
  {
      ......
      INS_KF.measured_vector[2] = acc.z;        // Z轴加速度
  }
*/

#include "kalman_filter.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* 私有函数声明 */
static void KF_AdjustHKR(KF_t *kf);

/**
 * @brief 初始化卡尔曼滤波器并分配矩阵内存
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @param xhat_size 状态向量维度
 * @param u_size 控制向量维度（无控制输入时设为0）
 * @param z_size 量测向量维度
 * @return int8_t 0对应没有错误
 */
int8_t KF_Init(KF_t *kf, uint8_t xhat_size, uint8_t u_size, uint8_t z_size) {
  if (kf == NULL) return -1;

  kf->xhat_size = xhat_size;
  kf->u_size = u_size;
  kf->z_size = z_size;

  kf->measurement_valid_num = 0;

  /* 量测标志分配 */
  kf->measurement_map = (uint8_t *)user_malloc(sizeof(uint8_t) * z_size);
  memset(kf->measurement_map, 0, sizeof(uint8_t) * z_size);

  kf->measurement_degree = (float *)user_malloc(sizeof(float) * z_size);
  memset(kf->measurement_degree, 0, sizeof(float) * z_size);

  kf->mat_r_diagonal_elements = (float *)user_malloc(sizeof(float) * z_size);
  memset(kf->mat_r_diagonal_elements, 0, sizeof(float) * z_size);

  kf->state_min_variance = (float *)user_malloc(sizeof(float) * xhat_size);
  memset(kf->state_min_variance, 0, sizeof(float) * xhat_size);

  kf->temp = (uint8_t *)user_malloc(sizeof(uint8_t) * z_size);
  memset(kf->temp, 0, sizeof(uint8_t) * z_size);

  /* 滤波数据分配 */
  kf->filtered_value = (float *)user_malloc(sizeof(float) * xhat_size);
  memset(kf->filtered_value, 0, sizeof(float) * xhat_size);

  kf->measured_vector = (float *)user_malloc(sizeof(float) * z_size);
  memset(kf->measured_vector, 0, sizeof(float) * z_size);

  kf->control_vector = (float *)user_malloc(sizeof(float) * u_size);
  memset(kf->control_vector, 0, sizeof(float) * u_size);

  /* 状态估计 xhat x(k|k) */
  kf->xhat_data = (float *)user_malloc(sizeof(float) * xhat_size);
  memset(kf->xhat_data, 0, sizeof(float) * xhat_size);
  KF_MatInit(&kf->xhat, kf->xhat_size, 1, kf->xhat_data);

  /* 先验状态估计 xhatminus x(k|k-1) */
  kf->xhatminus_data = (float *)user_malloc(sizeof(float) * xhat_size);
  memset(kf->xhatminus_data, 0, sizeof(float) * xhat_size);
  KF_MatInit(&kf->xhatminus, kf->xhat_size, 1, kf->xhatminus_data);

  /* 控制向量 u */
  if (u_size != 0) {
    kf->u_data = (float *)user_malloc(sizeof(float) * u_size);
    memset(kf->u_data, 0, sizeof(float) * u_size);
    KF_MatInit(&kf->u, kf->u_size, 1, kf->u_data);
  }

  /* 量测向量 z */
  kf->z_data = (float *)user_malloc(sizeof(float) * z_size);
  memset(kf->z_data, 0, sizeof(float) * z_size);
  KF_MatInit(&kf->z, kf->z_size, 1, kf->z_data);

  /* 协方差矩阵 P(k|k) */
  kf->P_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  memset(kf->P_data, 0, sizeof(float) * xhat_size * xhat_size);
  KF_MatInit(&kf->P, kf->xhat_size, kf->xhat_size, kf->P_data);

  /* 先验协方差矩阵 P(k|k-1) */
  kf->Pminus_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  memset(kf->Pminus_data, 0, sizeof(float) * xhat_size * xhat_size);
  KF_MatInit(&kf->Pminus, kf->xhat_size, kf->xhat_size, kf->Pminus_data);

  /* 状态转移矩阵 F 及其转置 FT */
  kf->F_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  kf->FT_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  memset(kf->F_data, 0, sizeof(float) * xhat_size * xhat_size);
  memset(kf->FT_data, 0, sizeof(float) * xhat_size * xhat_size);
  KF_MatInit(&kf->F, kf->xhat_size, kf->xhat_size, kf->F_data);
  KF_MatInit(&kf->FT, kf->xhat_size, kf->xhat_size, kf->FT_data);

  /* 控制矩阵 B */
  if (u_size != 0) {
    kf->B_data = (float *)user_malloc(sizeof(float) * xhat_size * u_size);
    memset(kf->B_data, 0, sizeof(float) * xhat_size * u_size);
    KF_MatInit(&kf->B, kf->xhat_size, kf->u_size, kf->B_data);
  }

  /* 量测矩阵 H 及其转置 HT */
  kf->H_data = (float *)user_malloc(sizeof(float) * z_size * xhat_size);
  kf->HT_data = (float *)user_malloc(sizeof(float) * xhat_size * z_size);
  memset(kf->H_data, 0, sizeof(float) * z_size * xhat_size);
  memset(kf->HT_data, 0, sizeof(float) * xhat_size * z_size);
  KF_MatInit(&kf->H, kf->z_size, kf->xhat_size, kf->H_data);
  KF_MatInit(&kf->HT, kf->xhat_size, kf->z_size, kf->HT_data);

  /* 过程噪声协方差矩阵 Q */
  kf->Q_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  memset(kf->Q_data, 0, sizeof(float) * xhat_size * xhat_size);
  KF_MatInit(&kf->Q, kf->xhat_size, kf->xhat_size, kf->Q_data);

  /* 量测噪声协方差矩阵 R */
  kf->R_data = (float *)user_malloc(sizeof(float) * z_size * z_size);
  memset(kf->R_data, 0, sizeof(float) * z_size * z_size);
  KF_MatInit(&kf->R, kf->z_size, kf->z_size, kf->R_data);

  /* 卡尔曼增益 K */
  kf->K_data = (float *)user_malloc(sizeof(float) * xhat_size * z_size);
  memset(kf->K_data, 0, sizeof(float) * xhat_size * z_size);
  KF_MatInit(&kf->K, kf->xhat_size, kf->z_size, kf->K_data);

  /* 临时矩阵分配 */
  kf->S_data = (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  kf->temp_matrix_data =
      (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  kf->temp_matrix_data1 =
      (float *)user_malloc(sizeof(float) * xhat_size * xhat_size);
  kf->temp_vector_data = (float *)user_malloc(sizeof(float) * xhat_size);
  kf->temp_vector_data1 = (float *)user_malloc(sizeof(float) * xhat_size);

  KF_MatInit(&kf->S, kf->xhat_size, kf->xhat_size, kf->S_data);
  KF_MatInit(&kf->temp_matrix, kf->xhat_size, kf->xhat_size,
             kf->temp_matrix_data);
  KF_MatInit(&kf->temp_matrix1, kf->xhat_size, kf->xhat_size,
             kf->temp_matrix_data1);
  KF_MatInit(&kf->temp_vector, kf->xhat_size, 1, kf->temp_vector_data);
  KF_MatInit(&kf->temp_vector1, kf->xhat_size, 1, kf->temp_vector_data1);

  /* 初始化跳过标志 */
  kf->skip_eq1 = 0;
  kf->skip_eq2 = 0;
  kf->skip_eq3 = 0;
  kf->skip_eq4 = 0;
  kf->skip_eq5 = 0;

  /* 初始化用户函数指针 */
  kf->User_Func0_f = NULL;
  kf->User_Func1_f = NULL;
  kf->User_Func2_f = NULL;
  kf->User_Func3_f = NULL;
  kf->User_Func4_f = NULL;
  kf->User_Func5_f = NULL;
  kf->User_Func6_f = NULL;

  return 0;
}

/**
 * @brief 获取量测并在启用自动调整时调整矩阵
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_Measure(KF_t *kf) {
  if (kf == NULL) return -1;

  /* 根据量测有效性自动调整 H, K, R 矩阵 */
  if (kf->use_auto_adjustment != 0) {
    KF_AdjustHKR(kf);
  } else {
    memcpy(kf->z_data, kf->measured_vector, sizeof(float) * kf->z_size);
    memset(kf->measured_vector, 0, sizeof(float) * kf->z_size);
  }

  memcpy(kf->u_data, kf->control_vector, sizeof(float) * kf->u_size);

  return 0;
}

/**
 * @brief 步骤1：先验状态估计 - xhat'(k) = F·xhat(k-1) + B·u
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_PredictState(KF_t *kf) {
  if (kf == NULL) return -1;

  if (!kf->skip_eq1) {
    if (kf->u_size > 0) {
      /* 有控制输入: xhat'(k) = F·xhat(k-1) + B·u */
      kf->temp_vector.numRows = kf->xhat_size;
      kf->temp_vector.numCols = 1;
      kf->mat_status = KF_MatMult(&kf->F, &kf->xhat, &kf->temp_vector);

      kf->temp_vector1.numRows = kf->xhat_size;
      kf->temp_vector1.numCols = 1;
      kf->mat_status = KF_MatMult(&kf->B, &kf->u, &kf->temp_vector1);
      kf->mat_status =
          KF_MatAdd(&kf->temp_vector, &kf->temp_vector1, &kf->xhatminus);
    } else {
      /* 无控制输入: xhat'(k) = F·xhat(k-1) */
      kf->mat_status = KF_MatMult(&kf->F, &kf->xhat, &kf->xhatminus);
    }
  }

  return 0;
}

/**
 * @brief 步骤2：先验协方差 - P'(k) = F·P(k-1)·F^T + Q
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_PredictCovariance(KF_t *kf) {
  if (kf == NULL) return -1;

  if (!kf->skip_eq2) {
    kf->mat_status = KF_MatTrans(&kf->F, &kf->FT);
    kf->mat_status = KF_MatMult(&kf->F, &kf->P, &kf->Pminus);
    kf->temp_matrix.numRows = kf->Pminus.numRows;
    kf->temp_matrix.numCols = kf->FT.numCols;
    /* F·P(k-1)·F^T */
    kf->mat_status = KF_MatMult(&kf->Pminus, &kf->FT, &kf->temp_matrix);
    kf->mat_status = KF_MatAdd(&kf->temp_matrix, &kf->Q, &kf->Pminus);
  }

  return 0;
}

/**
 * @brief 步骤3：卡尔曼增益 - K = P'(k)·H^T / (H·P'(k)·H^T + R)
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_CalcGain(KF_t *kf) {
  if (kf == NULL) return -1;

  if (!kf->skip_eq3) {
    kf->mat_status = KF_MatTrans(&kf->H, &kf->HT);
    kf->temp_matrix.numRows = kf->H.numRows;
    kf->temp_matrix.numCols = kf->Pminus.numCols;
    /* H·P'(k) */
    kf->mat_status = KF_MatMult(&kf->H, &kf->Pminus, &kf->temp_matrix);
    kf->temp_matrix1.numRows = kf->temp_matrix.numRows;
    kf->temp_matrix1.numCols = kf->HT.numCols;
    /* H·P'(k)·H^T */
    kf->mat_status = KF_MatMult(&kf->temp_matrix, &kf->HT, &kf->temp_matrix1);
    kf->S.numRows = kf->R.numRows;
    kf->S.numCols = kf->R.numCols;
    /* S = H·P'(k)·H^T + R */
    kf->mat_status = KF_MatAdd(&kf->temp_matrix1, &kf->R, &kf->S);
    /* S^-1 */
    kf->mat_status = KF_MatInv(&kf->S, &kf->temp_matrix1);
    kf->temp_matrix.numRows = kf->Pminus.numRows;
    kf->temp_matrix.numCols = kf->HT.numCols;
    /* P'(k)·H^T */
    kf->mat_status = KF_MatMult(&kf->Pminus, &kf->HT, &kf->temp_matrix);
    /* K = P'(k)·H^T·S^-1 */
    kf->mat_status = KF_MatMult(&kf->temp_matrix, &kf->temp_matrix1, &kf->K);
  }

  return 0;
}

/**
 * @brief 步骤4：状态更新 - xhat(k) = xhat'(k) + K·(z - H·xhat'(k))
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_UpdateState(KF_t *kf) {
  if (kf == NULL) return -1;

  if (!kf->skip_eq4) {
    kf->temp_vector.numRows = kf->H.numRows;
    kf->temp_vector.numCols = 1;
    /* H·xhat'(k) */
    kf->mat_status = KF_MatMult(&kf->H, &kf->xhatminus, &kf->temp_vector);
    kf->temp_vector1.numRows = kf->z.numRows;
    kf->temp_vector1.numCols = 1;
    /* 新息: z - H·xhat'(k) */
    kf->mat_status = KF_MatSub(&kf->z, &kf->temp_vector, &kf->temp_vector1);
    kf->temp_vector.numRows = kf->K.numRows;
    kf->temp_vector.numCols = 1;
    /* K·新息 */
    kf->mat_status = KF_MatMult(&kf->K, &kf->temp_vector1, &kf->temp_vector);
    /* xhat = xhat' + K·新息 */
    kf->mat_status = KF_MatAdd(&kf->xhatminus, &kf->temp_vector, &kf->xhat);
  }

  return 0;
}

/**
 * @brief 步骤5：协方差更新 - P(k) = P'(k) - K·H·P'(k)
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_UpdateCovariance(KF_t *kf) {
  if (kf == NULL) return -1;

  if (!kf->skip_eq5) {
    kf->temp_matrix.numRows = kf->K.numRows;
    kf->temp_matrix.numCols = kf->H.numCols;
    kf->temp_matrix1.numRows = kf->temp_matrix.numRows;
    kf->temp_matrix1.numCols = kf->Pminus.numCols;
    /* K·H */
    kf->mat_status = KF_MatMult(&kf->K, &kf->H, &kf->temp_matrix);
    /* K·H·P'(k) */
    kf->mat_status = KF_MatMult(&kf->temp_matrix, &kf->Pminus, &kf->temp_matrix1);
    /* P = P' - K·H·P' */
    kf->mat_status = KF_MatSub(&kf->Pminus, &kf->temp_matrix1, &kf->P);
  }

  return 0;
}

/**
 * @brief 执行完整的卡尔曼滤波周期（五大方程）
 *
 * 实现标准KF，并支持用户自定义函数钩子用于扩展（EKF/UKF/ESKF/AUKF）。
 * 每个步骤都可以通过 User_Func 回调函数替换。
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return float* 滤波后的状态估计值指针
 */
float *KF_Update(KF_t *kf) {
  if (kf == NULL) return NULL;

  /* 步骤0: 量测获取和矩阵调整 */
  KF_Measure(kf);
  if (kf->User_Func0_f != NULL) kf->User_Func0_f(kf);

  /* 步骤1: 先验状态估计 - xhat'(k) = F·xhat(k-1) + B·u */
  KF_PredictState(kf);
  if (kf->User_Func1_f != NULL) kf->User_Func1_f(kf);

  /* 步骤2: 先验协方差 - P'(k) = F·P(k-1)·F^T + Q */
  KF_PredictCovariance(kf);
  if (kf->User_Func2_f != NULL) kf->User_Func2_f(kf);

  /* 量测更新（仅在存在有效量测时执行） */
  if (kf->measurement_valid_num != 0 || kf->use_auto_adjustment == 0) {
    /* 步骤3: 卡尔曼增益 - K = P'(k)·H^T / (H·P'(k)·H^T + R) */
    KF_CalcGain(kf);
    if (kf->User_Func3_f != NULL) kf->User_Func3_f(kf);

    /* 步骤4: 状态更新 - xhat(k) = xhat'(k) + K·(z - H·xhat'(k)) */
    KF_UpdateState(kf);
    if (kf->User_Func4_f != NULL) kf->User_Func4_f(kf);

    /* 步骤5: 协方差更新 - P(k) = P'(k) - K·H·P'(k) */
    KF_UpdateCovariance(kf);
  } else {
    /* 无有效量测 - 仅预测 */
    memcpy(kf->xhat_data, kf->xhatminus_data, sizeof(float) * kf->xhat_size);
    memcpy(kf->P_data, kf->Pminus_data,
           sizeof(float) * kf->xhat_size * kf->xhat_size);
  }

  /* 后处理钩子 */
  if (kf->User_Func5_f != NULL) kf->User_Func5_f(kf);

  /* 防过度收敛：强制最小方差 */
  for (uint8_t i = 0; i < kf->xhat_size; i++) {
    if (kf->P_data[i * kf->xhat_size + i] < kf->state_min_variance[i])
      kf->P_data[i * kf->xhat_size + i] = kf->state_min_variance[i];
  }

  /* 复制结果到输出 */
  memcpy(kf->filtered_value, kf->xhat_data, sizeof(float) * kf->xhat_size);

  /* 附加后处理钩子 */
  if (kf->User_Func6_f != NULL) kf->User_Func6_f(kf);

  return kf->filtered_value;
}

/**
 * @brief 重置卡尔曼滤波器状态
 *
 * @param kf 卡尔曼滤波器结构体指针
 */
void KF_Reset(KF_t *kf) {
  if (kf == NULL) return;

  memset(kf->xhat_data, 0, sizeof(float) * kf->xhat_size);
  memset(kf->xhatminus_data, 0, sizeof(float) * kf->xhat_size);
  memset(kf->filtered_value, 0, sizeof(float) * kf->xhat_size);
  kf->measurement_valid_num = 0;
}

/**
 * @brief 根据量测有效性动态调整 H, R, K 矩阵
 *
 * 该函数根据当前周期中哪些量测有效（非零）来重建量测相关矩阵。
 * 支持具有不同采样率的异步传感器。
 *
 * @param kf 卡尔曼滤波器结构体指针
 */
static void KF_AdjustHKR(KF_t *kf) {
  kf->measurement_valid_num = 0;

  /* 复制并重置量测向量 */
  memcpy(kf->z_data, kf->measured_vector, sizeof(float) * kf->z_size);
  memset(kf->measured_vector, 0, sizeof(float) * kf->z_size);

  /* 清空 H 和 R 矩阵 */
  memset(kf->R_data, 0, sizeof(float) * kf->z_size * kf->z_size);
  memset(kf->H_data, 0, sizeof(float) * kf->xhat_size * kf->z_size);

  /* 识别有效量测并重建 z, H */
  for (uint8_t i = 0; i < kf->z_size; i++) {
    if (kf->z_data[i] != 0) { /* 非零表示有效量测 */
      /* 将有效量测压缩到 z */
      kf->z_data[kf->measurement_valid_num] = kf->z_data[i];
      kf->temp[kf->measurement_valid_num] = i;

      /* 重建 H 矩阵行 */
      kf->H_data[kf->xhat_size * kf->measurement_valid_num +
                 kf->measurement_map[i] - 1] = kf->measurement_degree[i];
      kf->measurement_valid_num++;
    }
  }

  /* 用有效量测方差重建 R 矩阵 */
  for (uint8_t i = 0; i < kf->measurement_valid_num; i++) {
    kf->R_data[i * kf->measurement_valid_num + i] =
        kf->mat_r_diagonal_elements[kf->temp[i]];
  }

  /* 调整矩阵维度以匹配有效量测数量 */
  kf->H.numRows = kf->measurement_valid_num;
  kf->H.numCols = kf->xhat_size;
  kf->HT.numRows = kf->xhat_size;
  kf->HT.numCols = kf->measurement_valid_num;
  kf->R.numRows = kf->measurement_valid_num;
  kf->R.numCols = kf->measurement_valid_num;
  kf->K.numRows = kf->xhat_size;
  kf->K.numCols = kf->measurement_valid_num;
  kf->z.numRows = kf->measurement_valid_num;
}

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
