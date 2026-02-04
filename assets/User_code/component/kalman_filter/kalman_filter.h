/*
  卡尔曼滤波器
  支持动态量测调整，使用ARM CMSIS DSP优化矩阵运算
*/

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include "arm_math.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* 内存分配配置 */
#ifndef user_malloc
#ifdef _CMSIS_OS_H
#define user_malloc pvPortMalloc /* FreeRTOS堆分配 */
#else
#define user_malloc malloc /* 标准C库分配 */
#endif
#endif

/* ARM CMSIS DSP 矩阵运算别名 */
#define KF_Mat              arm_matrix_instance_f32
#define KF_MatInit          arm_mat_init_f32
#define KF_MatAdd           arm_mat_add_f32
#define KF_MatSub           arm_mat_sub_f32
#define KF_MatMult          arm_mat_mult_f32
#define KF_MatTrans         arm_mat_trans_f32
#define KF_MatInv           arm_mat_inverse_f32

/* 卡尔曼滤波器主结构体 */
typedef struct KF_s {
  /* 输出和输入向量 */
  float *filtered_value;   /* 滤波后的状态估计输出 */
  float *measured_vector;  /* 量测输入向量 */
  float *control_vector;   /* 控制输入向量 */

  /* 维度 */
  uint8_t xhat_size; /* 状态向量维度 */
  uint8_t u_size;    /* 控制向量维度 */
  uint8_t z_size;    /* 量测向量维度 */

  /* 自动调整参数 */
  uint8_t use_auto_adjustment;    /* 启用动态 H/R/K 调整 */
  uint8_t measurement_valid_num;  /* 有效量测数量 */

  /* 量测配置 */
  uint8_t *measurement_map;        /* 量测到状态的映射 */
  float *measurement_degree;       /* 每个量测的H矩阵元素值 */
  float *mat_r_diagonal_elements;  /* 量测噪声方差（R对角线） */
  float *state_min_variance;       /* 最小状态方差（防过度收敛） */
  uint8_t *temp;                   /* 临时缓冲区 */

  /* 方程跳过标志（用于自定义用户函数） */
  uint8_t skip_eq1, skip_eq2, skip_eq3, skip_eq4, skip_eq5;

  /* 卡尔曼滤波器矩阵 */
  KF_Mat xhat;      /* 状态估计 x(k|k) */
  KF_Mat xhatminus; /* 先验状态估计 x(k|k-1) */
  KF_Mat u;         /* 控制向量 */
  KF_Mat z;         /* 量测向量 */
  KF_Mat P;         /* 后验误差协方差 P(k|k) */
  KF_Mat Pminus;    /* 先验误差协方差 P(k|k-1) */
  KF_Mat F, FT;     /* 状态转移矩阵及其转置 */
  KF_Mat B;         /* 控制矩阵 */
  KF_Mat H, HT;     /* 量测矩阵及其转置 */
  KF_Mat Q;         /* 过程噪声协方差 */
  KF_Mat R;         /* 量测噪声协方差 */
  KF_Mat K;         /* 卡尔曼增益 */
  KF_Mat S;         /* 临时矩阵 S */
  KF_Mat temp_matrix, temp_matrix1;   /* 临时矩阵 */
  KF_Mat temp_vector, temp_vector1;   /* 临时向量 */

  int8_t mat_status; /* 矩阵运算状态 */

  /* 用户自定义函数指针（用于EKF/UKF/ESKF扩展） */
  void (*User_Func0_f)(struct KF_s *kf); /* 自定义量测处理 */
  void (*User_Func1_f)(struct KF_s *kf); /* 自定义状态预测 */
  void (*User_Func2_f)(struct KF_s *kf); /* 自定义协方差预测 */
  void (*User_Func3_f)(struct KF_s *kf); /* 自定义卡尔曼增益计算 */
  void (*User_Func4_f)(struct KF_s *kf); /* 自定义状态更新 */
  void (*User_Func5_f)(struct KF_s *kf); /* 自定义后处理 */
  void (*User_Func6_f)(struct KF_s *kf); /* 附加自定义函数 */

  /* 矩阵数据存储指针 */
  float *xhat_data, *xhatminus_data;
  float *u_data;
  float *z_data;
  float *P_data, *Pminus_data;
  float *F_data, *FT_data;
  float *B_data;
  float *H_data, *HT_data;
  float *Q_data;
  float *R_data;
  float *K_data;
  float *S_data;
  float *temp_matrix_data, *temp_matrix_data1;
  float *temp_vector_data, *temp_vector_data1;
} KF_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/**
 * @brief 初始化卡尔曼滤波器并分配矩阵内存
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @param xhat_size 状态向量维度
 * @param u_size 控制向量维度（无控制输入时设为0）
 * @param z_size 量测向量维度
 * @return int8_t 0对应没有错误
 */
int8_t KF_Init(KF_t *kf, uint8_t xhat_size, uint8_t u_size, uint8_t z_size);

/**
 * @brief 获取量测并在启用自动调整时调整矩阵
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_Measure(KF_t *kf);

/**
 * @brief 步骤1：先验状态估计 - xhat'(k) = F·xhat(k-1) + B·u
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_PredictState(KF_t *kf);

/**
 * @brief 步骤2：先验协方差 - P'(k) = F·P(k-1)·F^T + Q
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_PredictCovariance(KF_t *kf);

/**
 * @brief 步骤3：卡尔曼增益 - K = P'(k)·H^T / (H·P'(k)·H^T + R)
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_CalcGain(KF_t *kf);

/**
 * @brief 步骤4：状态更新 - xhat(k) = xhat'(k) + K·(z - H·xhat'(k))
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_UpdateState(KF_t *kf);

/**
 * @brief 步骤5：协方差更新 - P(k) = P'(k) - K·H·P'(k)
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return int8_t 0对应没有错误
 */
int8_t KF_UpdateCovariance(KF_t *kf);

/**
 * @brief 执行完整的卡尔曼滤波周期（五大方程）
 *
 * @param kf 卡尔曼滤波器结构体指针
 * @return float* 滤波后的状态估计值指针
 */
float *KF_Update(KF_t *kf);

/**
 * @brief 重置卡尔曼滤波器状态
 *
 * @param kf 卡尔曼滤波器结构体指针
 */
void KF_Reset(KF_t *kf);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
