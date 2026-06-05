#pragma once

// RM 电机协议层接口定义。
// 负责将 RM C 驱动的 raw 反馈与电流控制能力包装成统一的 MotorProtocol 行为。

#include "device/motor/protocol/motor_protocol_fwd.hpp"
#include "device/motor/core/motor_install_spec.hpp"
#include "device/motor/core/motor_instance_config.hpp"
#include "device/motor/core/motor_state.hpp"
#include "device/motor/core/motor_traits.hpp"
#include "device/motor_rm.h"

namespace mr::motor {

struct RmProtocolDebugSnapshot {
    bool pending_valid = false;
    float pending_torque_current = 0.0f;
    float last_set_torque_nm = 0.0f;
    int8_t last_set_torque_ret = DEVICE_OK;
    int8_t last_commit_ret = DEVICE_OK;
    bool last_commit_skipped = false;
    uint8_t last_error_code = 0;
    bool rotor_position_initialized = false;
    bool angle_valid = false;
    uint32_t position_fault = 0;
    uint32_t large_delta_count = 0;
    float max_abs_delta_rad = 0.0f;
    uint32_t feedback_lost_count = 0;
    uint32_t last_feedback_tick = 0;
};

template <MotorModel Model>
class MotorProtocol<MotorKind::RM, Model> {
public:
    MotorProtocol(const MotorInstanceConfig<MotorKind::RM>& config,
                  const MotorInstallSpec& install,
                  MotorState& state,
                  MOTOR_RM_Module_t module);

    int8_t Register();
    int8_t Enable();
    int8_t Disable();
    int8_t Relax();
    int8_t Update();
    int8_t CommitCommand();
    bool HasPendingCommand() const { return pending_valid_; }
    void ClearPendingCommand();

    int8_t SetTorque(float torque_nm);
    int8_t SetZero();
    const RmProtocolDebugSnapshot& GetDebugSnapshot() const;

private:
    float TotalRatio() const;
    float ToTorqueCurrent(float output_torque_nm) const;
    void ResetStateCache();
    void RefreshStateCache();
    void ResetPositionTracker();
    void SyncRotorPosition(float single_turn_rotor_position_rad);
    void SetRotorPositionZero(float single_turn_rotor_position_rad);
    float AccumulateRotorPosition(float single_turn_rotor_position_rad, float rotor_velocity_rad_s, float dt_s);
    void MarkPositionInvalid(uint32_t fault_mask);
    void RefreshPositionDiagnostics(MotorState& next);
    float ApplyRotorPositionOffset(float rotor_position_rad) const;
    float ToOutputPosition(float rotor_position_rad) const;
    float ToOutputVelocity(float rotor_velocity_rad_s) const;
    float ToOutputTorque(float torque_current) const;
    bool TryGetRotorFeedback(float& rotor_position_rad,
                             float& rotor_velocity_rad_s,
                             float& torque_current,
                             float& temperature_c,
                             uint8_t& error_code) const;

    MotorInstanceConfig<MotorKind::RM> config_;
    MotorInstallSpec install_;
    MotorState& state_;
    MOTOR_RM_Param_t param_{};
    MOTOR_RM_t* instance_ = nullptr;
    MOTOR_RM_t vendor_instance_{};
    float pending_torque_current_ = 0.0f;
    bool pending_valid_ = false;
    RmProtocolDebugSnapshot debug_{};
    bool rotor_position_initialized_ = false;
    bool last_online_ = false;
    MotorProtocolState last_non_fault_protocol_state_ = MotorProtocolState::Unregistered;
    float last_single_turn_rotor_position_rad_ = 0.0f;
    float accumulated_rotor_position_rad_ = 0.0f;
    float rotor_zero_offset_rad_ = 0.0f;
    bool angle_valid_ = false;
    uint32_t position_fault_ = 0;
    uint32_t large_delta_count_ = 0;
    uint32_t feedback_lost_count_ = 0;
    uint32_t last_feedback_tick_ = 0;
    float max_abs_delta_rad_ = 0.0f;
};

} // namespace mr::motor
