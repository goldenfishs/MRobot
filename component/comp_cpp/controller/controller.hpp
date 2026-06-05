#pragma once

/*
 * C++ 控制律组件聚合头文件。
 *
 * 模块需要同时使用多种控制器时，直接包含这个头文件：
 *
 *   #include "component/controller/controller.hpp"
 *
 * 本文件包含所有控制器类型：
 *   - pid: 通用 PID 控制器
 *   - lqr: LQR 状态反馈控制器
 *   - mpc: 模型预测速度控制器
 */

#include "component/controller/controller_types.hpp"
#include "component/controller/lqr.hpp"
#include "component/controller/mpc.hpp"
#include "component/controller/pid.hpp"
