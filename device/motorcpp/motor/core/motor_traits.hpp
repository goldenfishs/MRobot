#pragma once

// 定义各电机 kind/model 组合的静态能力与参数表。
// 这里集中描述减速比、控制能力、量程等编译期特性。
// 具体型号只需要覆盖“确实有意义”的参数；未覆盖项沿用基类默认值。

#include <stdint.h>
#include <type_traits>

#include "device/motor/core/motor_capability.hpp"
#include "device/motor/core/motor_kind.hpp"
#include "device/motor/core/motor_model.hpp"
#include "device/motor_dm.h"
#include "device/motor_lz.h"
#include "device/motor_rm.h"

namespace mr::motor {

template <MotorKind Kind, MotorModel Model>
struct MotorModelValid : std::false_type {};

template <MotorKind Kind, MotorModel Model>
inline constexpr bool MotorModelValidV = MotorModelValid<Kind, Model>::value;

template <MotorKind Kind, MotorModel Model>
struct MotorTraits;

template <>
struct MotorModelValid<MotorKind::RM, MotorModel::M2006> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::RM, MotorModel::M3508> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::RM, MotorModel::M6020> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J10010> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J10010L> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J10422P> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J3507> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J4310> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J4310P> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J4340> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J4340P> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J6006> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J6248P> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J8006> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J8009> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::J8009P> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::DM, MotorModel::H3510> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO0> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO1> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO2> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO3> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO4> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO5> : std::true_type {};
template <>
struct MotorModelValid<MotorKind::LZ, MotorModel::RSO6> : std::true_type {};

template <MotorKind KindValue, MotorModel ModelValue>
struct MotorTraitsBase {
    static constexpr MotorKind kKind = KindValue;                    // 电机种类（协议类别），如 RM / DM / LZ。
    static constexpr MotorModel kModel = ModelValue;                // 电机型号，如 M3508 / J4310 / RSO3。
    static constexpr float kGearRatio = 1.0f;                       // 电机内部减速比；输出轴物理量换算时会与外部减速比共同参与计算，无减速时为 1.0。
    static constexpr bool kSupportsMit = false;                     // 是否支持 MIT（位置/速度/Kp/Kd/前馈力矩）复合控制接口。
    static constexpr bool kSupportsTorque = false;                  // 是否支持力矩/电流控制接口。
    static constexpr bool kSupportsVelocity = false;                // 是否支持速度控制接口。
    static constexpr bool kSupportsPosition = false;                // 是否支持位置控制接口。
    static constexpr bool kIsMultiTurn = false;                     // 反馈位置是否天然支持多圈连续语义，或可由协议层稳定累计为多圈。
    static constexpr bool kHasNativeZeroSet = false;                // 电机协议是否原生支持设零/保存零点。
    static constexpr bool kHasHostId = false;                       // 运行时配置中是否需要 host_id 一类主机标识。
    static constexpr bool kHasMasterId = false;                     // 运行时配置中是否需要 master_id 一类主控标识。
    static constexpr float kDefaultKp = 0.0f;                       // 默认比例增益 Kp，通常用于 MIT 或上层控制器初始化参考。
    static constexpr float kDefaultKd = 0.0f;                       // 默认微分增益 Kd，通常用于 MIT 或上层控制器初始化参考。
    static constexpr float kRatedVoltage = 0.0f;                    // 额定供电电压，单位 V。
    static constexpr float kMaxSupplyVoltage = 0.0f;                // 手册标称支持的最高供电电压，单位 V。
    static constexpr float kMinPosition = 0.0f;                     // 位置下限，单位 rad；为 0 表示未给出限制。
    static constexpr float kMaxPosition = 0.0f;                     // 位置上限，单位 rad；为 0 表示未给出限制。
    static constexpr float kMaxTorque = 0.0f;                       // 最大输出力矩，单位 N·m；通常用于命令裁剪。
    static constexpr float kMaxVelocity = 0.0f;                     // 最大输出角速度，单位 rad/s；通常用于命令裁剪。
    static constexpr float kRecommendedCurrent = 0.0f;              // 推荐持续工作电流，单位 A。
    static constexpr float kRatedCurrent = 0.0f;                    // 额定电流，单位 A。
    static constexpr float kPeakCurrent = 0.0f;                     // 峰值电流，单位 A。
    static constexpr float kNoLoadCurrent = 0.0f;                   // 空载电流，单位 A。
    static constexpr float kRatedSupplyCurrent = 0.0f;              // 额定电源侧电流，单位 A。
    static constexpr float kPeakSupplyCurrent = 0.0f;               // 峰值电源侧电流，单位 A。
    static constexpr float kRawCurrentRange = 0.0f;                 // 协议原始电流指令/反馈满量程绝对值，例如 16384 / 10000 / 30000。
    static constexpr float kCurrentRangeAmp = 0.0f;                 // 原始电流满量程映射到的物理电流绝对值，单位 A。
    static constexpr float kRecommendedVelocity = 0.0f;             // 推荐持续工作角速度，单位 rad/s。
    static constexpr float kRatedVelocity = 0.0f;                   // 额定角速度，单位 rad/s。
    static constexpr float kNoLoadVelocity = 0.0f;                  // 空载最大角速度，单位 rad/s。
    static constexpr float kRatedTorque = 0.0f;                     // 额定输出力矩，单位 N·m。
    static constexpr float kPeakTorque = 0.0f;                      // 峰值输出力矩，单位 N·m。
    static constexpr float kTorqueConstant = 0.0f;                  // 电机轴（转子轴）力矩常数；仅适用于需要固定电流-力矩换算的型号。
    static constexpr float kReducerRatio = 1.0f;                    // 手册标称关节减速比；DM 协议按输出轴物理量通信时不参与命令换算。
    static constexpr uint32_t kEncoderCpr = 0;                      // 编码器每圈计数（counts per revolution）；未知时为 0。
    static constexpr float kWeightGram = 0.0f;                      // 电机重量，单位 g。
    static constexpr MotorCapability kCapabilities = MotorCapability::None; // 编译期能力位掩码，汇总支持的控制能力。
    static constexpr const char* kName = "Unknown";                // 人类可读型号名，便于调试输出。
};

template <>
struct MotorTraits<MotorKind::RM, MotorModel::M2006> : MotorTraitsBase<MotorKind::RM, MotorModel::M2006> {
    static constexpr MOTOR_RM_Module_t kVendorModule = MOTOR_M2006;
    static constexpr float kGearRatio = 36.0f;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr bool kHasNativeZeroSet = true;
    static constexpr float kMaxTorque = 1.8f;
    static constexpr float kMaxVelocity = 45.0f;
    static constexpr float kRecommendedCurrent = 3.0f;
    static constexpr float kRatedCurrent = 3.0f;
    static constexpr float kPeakCurrent = 10.0f;
    static constexpr float kRawCurrentRange = 10000.0f;
    static constexpr float kCurrentRangeAmp = 10.0f;
    static constexpr float kRecommendedVelocity = 45.0f;
    static constexpr float kRatedVelocity = 45.0f;
    static constexpr float kNoLoadVelocity = 52.36f;
    static constexpr float kRatedTorque = 1.0f;
    static constexpr float kPeakTorque = 1.8f;
    static constexpr float kTorqueConstant = 0.005f;
    static constexpr uint16_t kEncoderCpr = 8192;
    static constexpr MotorCapability kCapabilities = MotorCapability::Current;
    static constexpr const char* kName = "RM-M2006";
};

template <>
struct MotorTraits<MotorKind::RM, MotorModel::M3508> : MotorTraitsBase<MotorKind::RM, MotorModel::M3508> {
    static constexpr MOTOR_RM_Module_t kVendorModule = MOTOR_M3508;
    static constexpr float kGearRatio = 3591.0f / 187.0f;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr bool kHasNativeZeroSet = true;
    static constexpr float kMaxTorque = 4.5f;
    static constexpr float kMaxVelocity = 49.11f;
    static constexpr float kRecommendedCurrent = 10.0f;
    static constexpr float kRatedCurrent = 10.0f;
    static constexpr float kPeakCurrent = 20.0f;
    static constexpr float kRawCurrentRange = 16384.0f;
    static constexpr float kCurrentRangeAmp = 20.0f;
    static constexpr float kRecommendedVelocity = 49.11f;
    static constexpr float kRatedVelocity = 49.11f;
    static constexpr float kNoLoadVelocity = 50.47f;
    static constexpr float kRatedTorque = 3.0f;
    static constexpr float kPeakTorque = 4.5f;
    static constexpr float kTorqueConstant = 0.015622389f;
    static constexpr uint16_t kEncoderCpr = 8192;
    static constexpr MotorCapability kCapabilities = MotorCapability::Current;
    static constexpr const char* kName = "RM-M3508";
};

template <>
struct MotorTraits<MotorKind::RM, MotorModel::M6020> : MotorTraitsBase<MotorKind::RM, MotorModel::M6020> {
    static constexpr MOTOR_RM_Module_t kVendorModule = MOTOR_GM6020;
    static constexpr float kGearRatio = 1.0f;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr float kMaxTorque = 1.2f;
    static constexpr float kMaxVelocity = 33.51f;
    static constexpr float kRecommendedCurrent = 1.62f;
    static constexpr float kRatedCurrent = 1.62f;
    static constexpr float kPeakCurrent = 3.0f;
    static constexpr float kRawCurrentRange = 30000.0f;
    static constexpr float kCurrentRangeAmp = 3.0f;
    static constexpr float kRecommendedVelocity = 13.82f;
    static constexpr float kRatedVelocity = 13.82f;
    static constexpr float kNoLoadVelocity = 33.51f;
    static constexpr float kRatedTorque = 1.2f;
    static constexpr float kPeakTorque = 1.2f;
    static constexpr float kTorqueConstant = 0.741f;
    static constexpr uint16_t kEncoderCpr = 8192;
    static constexpr MotorCapability kCapabilities = MotorCapability::Current;
    static constexpr const char* kName = "RM-M6020";
};

constexpr float MotorTraitsRpmToRadPerSec(float rpm) {
    return rpm * 2.0f * 3.14159265358979323846f / 60.0f;
}

constexpr uint32_t MotorTraitsEncoderCprFromBits(uint8_t bits) {
    return (1u << bits) - 1u;
}

template <MotorModel Model, MOTOR_DM_Module_t Module>
struct DmJointMotorTraits : MotorTraitsBase<MotorKind::DM, Model> {
    static constexpr MOTOR_DM_Module_t kVendorModule = Module;
    static constexpr bool kSupportsMit = true;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kSupportsVelocity = true;
    static constexpr bool kSupportsPosition = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr bool kHasNativeZeroSet = true;
    static constexpr bool kHasMasterId = true;
    static constexpr float kDefaultKp = 0.0f;
    static constexpr float kDefaultKd = 0.0f;
    static constexpr float kMinPosition = -12.56637f;
    static constexpr float kMaxPosition = 12.56637f;
    static constexpr MotorCapability kCapabilities = MotorCapability::Current | MotorCapability::Velocity | MotorCapability::Position | MotorCapability::MIT;
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J10010> : DmJointMotorTraits<MotorModel::J10010, MOTOR_DM_J10010> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 150.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kRecommendedCurrent = 20.0f;
    static constexpr float kRatedCurrent = 20.0f;
    static constexpr float kPeakCurrent = 70.0f;
    static constexpr float kRatedSupplyCurrent = 20.0f;
    static constexpr float kPeakSupplyCurrent = 70.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kRatedTorque = 40.0f;
    static constexpr float kPeakTorque = 150.0f;
    static constexpr float kTorqueConstant = 40.0f / 20.0f / 10.0f;
    static constexpr float kReducerRatio = 10.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J10010-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J10010L> : DmJointMotorTraits<MotorModel::J10010L, MOTOR_DM_J10010L> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 120.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRecommendedCurrent = 23.5f;
    static constexpr float kRatedCurrent = 23.5f;
    static constexpr float kPeakCurrent = 95.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(70.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(70.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedTorque = 40.0f;
    static constexpr float kPeakTorque = 120.0f;
    static constexpr float kTorqueConstant = 40.0f / 23.5f / 10.0f;
    static constexpr float kReducerRatio = 10.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J10010L-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J10422P> : DmJointMotorTraits<MotorModel::J10422P, MOTOR_DM_J10422P> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 400.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kRecommendedCurrent = 27.5f;
    static constexpr float kRatedCurrent = 44.5f;
    static constexpr float kPeakCurrent = 165.0f;
    static constexpr float kRatedSupplyCurrent = 27.5f;
    static constexpr float kPeakSupplyCurrent = 48.9f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kRatedTorque = 100.0f;
    static constexpr float kPeakTorque = 400.0f;
    static constexpr float kTorqueConstant = 100.0f / 44.5f / 22.0f;
    static constexpr float kReducerRatio = 22.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(17);
    static constexpr const char* kName = "DM-J10422P-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J3507> : DmJointMotorTraits<MotorModel::J3507, MOTOR_DM_J3507> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 3.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(460.0f);
    static constexpr float kRecommendedCurrent = 1.2f;
    static constexpr float kRatedCurrent = 3.0f;
    static constexpr float kPeakCurrent = 8.3f;
    static constexpr float kRatedSupplyCurrent = 1.2f;
    static constexpr float kPeakSupplyCurrent = 4.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(460.0f);
    static constexpr float kRatedTorque = 0.8f;
    static constexpr float kPeakTorque = 3.0f;
    static constexpr float kTorqueConstant = 0.8f / 3.0f / 7.0f;
    static constexpr float kReducerRatio = 7.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J3507-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J4310> : DmJointMotorTraits<MotorModel::J4310, MOTOR_DM_J4310> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 12.5f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRecommendedCurrent = 3.1f;
    static constexpr float kRatedCurrent = 4.9f;
    static constexpr float kPeakCurrent = 20.0f;
    static constexpr float kRatedSupplyCurrent = 3.1f;
    static constexpr float kPeakSupplyCurrent = 16.5f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRatedTorque = 3.5f;
    static constexpr float kPeakTorque = 12.5f;
    static constexpr float kTorqueConstant = 3.5f / 4.9f / 10.0f;
    static constexpr float kReducerRatio = 10.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(16);
    static constexpr const char* kName = "DM-J4310-2EC-V1.2-24V";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J4310P> : DmJointMotorTraits<MotorModel::J4310P, MOTOR_DM_J4310P> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 12.5f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRecommendedCurrent = 3.1f;
    static constexpr float kRatedCurrent = 4.9f;
    static constexpr float kPeakCurrent = 20.0f;
    static constexpr float kRatedSupplyCurrent = 3.1f;
    static constexpr float kPeakSupplyCurrent = 16.5f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRatedTorque = 3.5f;
    static constexpr float kPeakTorque = 12.5f;
    static constexpr float kTorqueConstant = 3.5f / 4.9f / 10.0f;
    static constexpr float kReducerRatio = 10.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(16);
    static constexpr const char* kName = "DM-J4310P-2EC-24V";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J4340> : DmJointMotorTraits<MotorModel::J4340, MOTOR_DM_J4340> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 40.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(56.0f);
    static constexpr float kRecommendedCurrent = 3.1f;
    static constexpr float kRatedCurrent = 4.11f;
    static constexpr float kPeakCurrent = 19.85f;
    static constexpr float kRatedSupplyCurrent = 3.1f;
    static constexpr float kPeakSupplyCurrent = 16.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(36.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(36.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(56.0f);
    static constexpr float kRatedTorque = 14.0f;
    static constexpr float kPeakTorque = 40.0f;
    static constexpr float kTorqueConstant = 14.0f / 4.11f / 40.0f;
    static constexpr float kReducerRatio = 40.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J4340-2EC-24V";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J4340P> : DmJointMotorTraits<MotorModel::J4340P, MOTOR_DM_J4340P> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 40.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(56.0f);
    static constexpr float kRecommendedCurrent = 3.1f;
    static constexpr float kRatedCurrent = 4.11f;
    static constexpr float kPeakCurrent = 19.85f;
    static constexpr float kRatedSupplyCurrent = 3.1f;
    static constexpr float kPeakSupplyCurrent = 16.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(36.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(36.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(56.0f);
    static constexpr float kRatedTorque = 14.0f;
    static constexpr float kPeakTorque = 40.0f;
    static constexpr float kTorqueConstant = 14.0f / 4.11f / 40.0f;
    static constexpr float kReducerRatio = 40.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J4340P-2EC-24V";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J6006> : DmJointMotorTraits<MotorModel::J6006, MOTOR_DM_J6006> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 12.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(240.0f);
    static constexpr float kRecommendedCurrent = 4.0f;
    static constexpr float kRatedCurrent = 4.0f;
    static constexpr float kPeakCurrent = 13.0f;
    static constexpr float kRatedSupplyCurrent = 4.0f;
    static constexpr float kPeakSupplyCurrent = 13.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(150.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(240.0f);
    static constexpr float kRatedTorque = 4.0f;
    static constexpr float kPeakTorque = 12.0f;
    static constexpr float kTorqueConstant = 4.0f / 4.0f / 6.0f;
    static constexpr float kReducerRatio = 6.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J6006-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J6248P> : DmJointMotorTraits<MotorModel::J6248P, MOTOR_DM_J6248P> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 97.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(60.0f);
    static constexpr float kRecommendedCurrent = 7.0f;
    static constexpr float kRatedCurrent = 11.3f;
    static constexpr float kPeakCurrent = 38.7f;
    static constexpr float kRatedSupplyCurrent = 7.0f;
    static constexpr float kPeakSupplyCurrent = 16.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(40.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(40.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(60.0f);
    static constexpr float kRatedTorque = 30.0f;
    static constexpr float kPeakTorque = 97.0f;
    static constexpr float kTorqueConstant = 30.0f / 11.3f / 48.0f;
    static constexpr float kReducerRatio = 48.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(16);
    static constexpr const char* kName = "DM-J6248P-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J8006> : DmJointMotorTraits<MotorModel::J8006, MOTOR_DM_J8006> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 20.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRecommendedCurrent = 9.0f;
    static constexpr float kRatedCurrent = 9.0f;
    static constexpr float kPeakCurrent = 21.0f;
    static constexpr float kRatedSupplyCurrent = 9.0f;
    static constexpr float kPeakSupplyCurrent = 21.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(120.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRatedTorque = 8.0f;
    static constexpr float kPeakTorque = 20.0f;
    static constexpr float kTorqueConstant = 8.0f / 9.0f / 6.0f;
    static constexpr float kReducerRatio = 6.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J8006-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J8009> : DmJointMotorTraits<MotorModel::J8009, MOTOR_DM_J8009> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 40.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(160.0f);
    static constexpr float kRecommendedCurrent = 20.0f;
    static constexpr float kRatedCurrent = 20.0f;
    static constexpr float kPeakCurrent = 50.0f;
    static constexpr float kRatedSupplyCurrent = 20.0f;
    static constexpr float kPeakSupplyCurrent = 50.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(160.0f);
    static constexpr float kRatedTorque = 20.0f;
    static constexpr float kPeakTorque = 40.0f;
    static constexpr float kTorqueConstant = 20.0f / 20.0f / 9.0f;
    static constexpr float kReducerRatio = 9.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J8009-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::J8009P> : DmJointMotorTraits<MotorModel::J8009P, MOTOR_DM_J8009P> {
    static constexpr float kRatedVoltage = 24.0f;
    static constexpr float kMaxSupplyVoltage = 48.0f;
    static constexpr float kMaxTorque = 40.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(160.0f);
    static constexpr float kRecommendedCurrent = 20.0f;
    static constexpr float kRatedCurrent = 20.0f;
    static constexpr float kPeakCurrent = 40.0f;
    static constexpr float kRatedSupplyCurrent = 20.0f;
    static constexpr float kPeakSupplyCurrent = 40.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(160.0f);
    static constexpr float kRatedTorque = 20.0f;
    static constexpr float kPeakTorque = 40.0f;
    static constexpr float kTorqueConstant = 20.0f / 20.0f / 9.0f;
    static constexpr float kReducerRatio = 9.0f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr const char* kName = "DM-J8009P-2EC";
};

template <>
struct MotorTraits<MotorKind::DM, MotorModel::H3510> : MotorTraitsBase<MotorKind::DM, MotorModel::H3510> {
    static constexpr MOTOR_DM_Module_t kVendorModule = MOTOR_DM_H3510;
    static constexpr bool kSupportsMit = true;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kSupportsVelocity = true;
    static constexpr bool kSupportsPosition = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr bool kHasNativeZeroSet = true;
    static constexpr bool kHasMasterId = true;
    static constexpr float kDefaultKp = 0.0f;
    static constexpr float kDefaultKd = 0.0f;
    static constexpr float kMaxTorque = 0.45f;  // 峰值扭矩 0.45 Nm
    static constexpr float kMaxVelocity = 188.5f;  // 空载最大 1800 rpm
    static constexpr float kRecommendedCurrent = 1.1f;  // 额定电流 1.1A
    static constexpr float kRatedCurrent = 1.1f;
    static constexpr float kPeakCurrent = 3.2f;  // 峰值电流 3.2A
    static constexpr float kRecommendedVelocity = 52.36f;  // 额定转速 500 rpm
    static constexpr float kRatedVelocity = 52.36f;
    static constexpr float kNoLoadVelocity = 188.5f;
    static constexpr float kRatedTorque = 0.18f;  // 额定扭矩 0.18 Nm
    static constexpr float kPeakTorque = 0.45f;
    static constexpr uint32_t kEncoderCpr = 65536;
    static constexpr MotorCapability kCapabilities = MotorCapability::Current | MotorCapability::Velocity | MotorCapability::Position | MotorCapability::MIT;
    static constexpr const char* kName = "DM-H3510";
};

template <MotorModel Model, MOTOR_LZ_Module_t Module>
struct LzRsMotorTraits : MotorTraitsBase<MotorKind::LZ, Model> {
    static constexpr MOTOR_LZ_Module_t kVendorModule = Module;
    static constexpr bool kSupportsMit = true;
    static constexpr bool kSupportsTorque = true;
    static constexpr bool kSupportsVelocity = true;
    static constexpr bool kSupportsPosition = true;
    static constexpr bool kIsMultiTurn = true;
    static constexpr bool kHasNativeZeroSet = true;
    static constexpr bool kHasHostId = true;
    static constexpr float kMaxPosition = 12.57f;
    static constexpr uint32_t kEncoderCpr = MotorTraitsEncoderCprFromBits(14);
    static constexpr MotorCapability kCapabilities = MotorCapability::Current | MotorCapability::Velocity | MotorCapability::Position | MotorCapability::MIT;
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO0> : LzRsMotorTraits<MotorModel::RSO0, MOTOR_LZ_RSO0> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 14.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(315.0f);
    static constexpr float kNoLoadCurrent = 0.5f;
    static constexpr float kRatedCurrent = 4.7f;
    static constexpr float kPeakCurrent = 15.5f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(315.0f);
    static constexpr float kRatedTorque = 5.0f;
    static constexpr float kPeakTorque = 14.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 10.0f;
    static constexpr float kWeightGram = 310.0f;
    static constexpr const char* kName = "LZ-RS00";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO1> : LzRsMotorTraits<MotorModel::RSO1, MOTOR_LZ_RSO1> {
    static constexpr float kRatedVoltage = 36.0f;
    static constexpr float kMaxSupplyVoltage = 50.0f;
    static constexpr float kMaxTorque = 17.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(315.0f);
    static constexpr float kNoLoadCurrent = 0.5f;
    static constexpr float kRatedCurrent = 7.0f;
    static constexpr float kPeakCurrent = 23.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(315.0f);
    static constexpr float kRatedTorque = 6.0f;
    static constexpr float kPeakTorque = 17.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 7.75f;
    static constexpr float kWeightGram = 380.0f;
    static constexpr const char* kName = "LZ-RS01";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO2> : LzRsMotorTraits<MotorModel::RSO2, MOTOR_LZ_RSO2> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 17.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(410.0f);
    static constexpr float kNoLoadCurrent = 0.5f;
    static constexpr float kRatedCurrent = 7.0f;
    static constexpr float kPeakCurrent = 23.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(410.0f);
    static constexpr float kRatedTorque = 6.0f;
    static constexpr float kPeakTorque = 17.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 7.75f;
    static constexpr float kWeightGram = 405.0f;
    static constexpr const char* kName = "LZ-RS02";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO3> : LzRsMotorTraits<MotorModel::RSO3, MOTOR_LZ_RSO3> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 60.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(195.0f);
    static constexpr float kNoLoadCurrent = 2.0f;
    static constexpr float kRatedCurrent = 13.0f;
    static constexpr float kPeakCurrent = 43.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(195.0f);
    static constexpr float kRatedTorque = 20.0f;
    static constexpr float kPeakTorque = 60.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 9.0f;
    static constexpr float kWeightGram = 880.0f;
    static constexpr const char* kName = "LZ-RS03";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO4> : LzRsMotorTraits<MotorModel::RSO4, MOTOR_LZ_RSO4> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 120.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kNoLoadCurrent = 2.0f;
    static constexpr float kRatedCurrent = 27.0f;
    static constexpr float kPeakCurrent = 90.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(50.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(50.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(200.0f);
    static constexpr float kRatedTorque = 40.0f;
    static constexpr float kPeakTorque = 120.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 9.0f;
    static constexpr float kWeightGram = 1420.0f;
    static constexpr const char* kName = "LZ-RS04";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO5> : LzRsMotorTraits<MotorModel::RSO5, MOTOR_LZ_RSO5> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 5.5f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(480.0f);
    static constexpr float kNoLoadCurrent = 0.14f;
    static constexpr float kRatedCurrent = 2.4f;
    static constexpr float kPeakCurrent = 11.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(480.0f);
    static constexpr float kRatedTorque = 1.6f;
    static constexpr float kPeakTorque = 5.5f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 7.75f;
    static constexpr float kWeightGram = 191.0f;
    static constexpr const char* kName = "LZ-RS05";
};

template <>
struct MotorTraits<MotorKind::LZ, MotorModel::RSO6> : LzRsMotorTraits<MotorModel::RSO6, MOTOR_LZ_RSO6> {
    static constexpr float kRatedVoltage = 48.0f;
    static constexpr float kMaxSupplyVoltage = 60.0f;
    static constexpr float kMaxTorque = 36.0f;
    static constexpr float kMaxVelocity = MotorTraitsRpmToRadPerSec(480.0f);
    static constexpr float kNoLoadCurrent = 0.98f;
    static constexpr float kRatedCurrent = 14.3f;
    static constexpr float kPeakCurrent = 57.0f;
    static constexpr float kRecommendedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kRatedVelocity = MotorTraitsRpmToRadPerSec(100.0f);
    static constexpr float kNoLoadVelocity = MotorTraitsRpmToRadPerSec(480.0f);
    static constexpr float kRatedTorque = 11.0f;
    static constexpr float kPeakTorque = 36.0f;
    static constexpr float kTorqueConstant = 1.0f;
    static constexpr float kReducerRatio = 9.0f;
    static constexpr float kWeightGram = 621.0f;
    static constexpr const char* kName = "LZ-RS06";
};

} // namespace mr::motor
