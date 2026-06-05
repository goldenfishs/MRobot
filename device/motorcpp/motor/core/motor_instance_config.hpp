#pragma once

// 定义按 MotorKind 分类的实例配置结构。
// 用于在通用 motor 配置与底层厂商参数结构之间做集中转换。

#include <stdint.h>

#include "bsp/can.h"
#include "device/motor/core/motor_kind.hpp"
#include "device/motor_dm.h"
#include "device/motor_lz.h"
#include "device/motor_rm.h"

namespace mr::motor {

template <MotorKind Kind>
struct MotorInstanceConfig;

template <>
struct MotorInstanceConfig<MotorKind::RM> {
    BSP_CAN_t can = BSP_CAN_1;
    uint16_t id = 0;
    bool reverse = false;

    static constexpr MotorInstanceConfig FromVendorParam(const MOTOR_RM_Param_t& param) {
        return MotorInstanceConfig{param.can, param.id, param.reverse};
    }

    constexpr MOTOR_RM_Param_t ToVendorParam(MOTOR_RM_Module_t module) const {
        return MOTOR_RM_Param_t{can, id, module, reverse, false};
    }
};

template <>
struct MotorInstanceConfig<MotorKind::DM> {
    BSP_CAN_t can = BSP_CAN_1;
    uint16_t master_id = 0;
    uint16_t can_id = 0;
    bool reverse = false;

    static constexpr MotorInstanceConfig FromVendorParam(const MOTOR_DM_Param_t& param) {
        return MotorInstanceConfig{param.can, param.master_id, param.can_id, param.reverse};
    }

    constexpr MOTOR_DM_Param_t ToVendorParam(MOTOR_DM_Module_t module) const {
        return MOTOR_DM_Param_t{can, master_id, can_id, module, reverse};
    }
};

template <>
struct MotorInstanceConfig<MotorKind::LZ> {
    BSP_CAN_t can = BSP_CAN_1;
    uint8_t motor_id = 0;
    uint8_t host_id = 0xff;
    MOTOR_LZ_ControlMode_t mode = MOTOR_LZ_MODE_MOTION;
    bool reverse = false;

    static constexpr MotorInstanceConfig FromVendorParam(const MOTOR_LZ_Param_t& param) {
        return MotorInstanceConfig{param.can, param.motor_id, param.host_id, param.mode, param.reverse};
    }

    constexpr MOTOR_LZ_Param_t ToVendorParam(MOTOR_LZ_Module_t module) const {
        return MOTOR_LZ_Param_t{can, motor_id, host_id, module, reverse, mode};
    }
};

} // namespace mr::motor