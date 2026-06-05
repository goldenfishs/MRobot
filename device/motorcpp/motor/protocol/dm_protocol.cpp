#include "device/motor/protocol/dm_protocol.hpp"

#include "component/math/scalar.hpp"
#include "component/user_math.h"
#include "device/device.h"

namespace mr::motor {

namespace {

float ResolvePositiveRatio(float ratio) {
    return mr::component::math::positive_or(ratio, 1.0f);
}

constexpr float kPi = 3.14159265358979323846f;
constexpr float kTwoPi = 6.28318530717958647692f;
constexpr float kDmPositionMin = -12.56637f;
constexpr float kDmPositionMax = 12.56637f;
constexpr float kDmPositionSpan = kDmPositionMax - kDmPositionMin;
constexpr float kDmPositionHalfSpan = 0.5f * kDmPositionSpan;
constexpr float kDefaultResyncDeltaRad = 1.75f * kPi;
constexpr float kDmVelocityMin = -30.0f;
constexpr float kDmVelocityMax = 30.0f;
constexpr float kDmTorqueMin = -12.0f;
constexpr float kDmTorqueMax = 12.0f;

float UintToFloat(uint16_t raw, float min_value, float max_value, int bits) {
    const float span = max_value - min_value;
    return (static_cast<float>(raw) * span / static_cast<float>((1 << bits) - 1)) + min_value;
}

float WrapToPi(float angle_rad) {
    return mr::component::math::wrap_to_pi(angle_rad);
}

float WrapDmAngleDiff(float diff_rad) {
    return mr::component::math::wrap_error(diff_rad, kDmPositionSpan);
}

uint32_t EncodeDmFault(MOTOR_DM_Status_t status) {
    switch (status) {
        case MOTOR_DM_STATUS_OVERVOLTAGE: return (1u << 0);
        case MOTOR_DM_STATUS_UNDERVOLTAGE: return (1u << 1);
        case MOTOR_DM_STATUS_OVERCURRENT: return (1u << 2);
        case MOTOR_DM_STATUS_MOS_OVERTEMP: return (1u << 3);
        case MOTOR_DM_STATUS_COIL_OVERTEMP: return (1u << 4);
        case MOTOR_DM_STATUS_COMM_LOST: return (1u << 5);
        case MOTOR_DM_STATUS_OVERLOAD: return (1u << 6);
        default: return 0u;
    }
}

MotorProtocolState DecodeDmProtocolState(MOTOR_DM_Status_t status) {
    switch (status) {
        case MOTOR_DM_STATUS_ENABLED:
            return MotorProtocolState::Enabled;
        case MOTOR_DM_STATUS_DISABLED:
            return MotorProtocolState::Disabled;
        case MOTOR_DM_STATUS_OVERVOLTAGE:
        case MOTOR_DM_STATUS_UNDERVOLTAGE:
        case MOTOR_DM_STATUS_OVERCURRENT:
        case MOTOR_DM_STATUS_MOS_OVERTEMP:
        case MOTOR_DM_STATUS_COIL_OVERTEMP:
        case MOTOR_DM_STATUS_COMM_LOST:
        case MOTOR_DM_STATUS_OVERLOAD:
            return MotorProtocolState::Fault;
        default:
            return MotorProtocolState::Registered;
    }
}

} // namespace

template <MotorModel Model>
MotorProtocol<MotorKind::DM, Model>::MotorProtocol(const MotorInstanceConfig<MotorKind::DM>& config,
                                            const MotorInstallSpec& install,
                                            MotorState& state,
                                            MOTOR_DM_Module_t module)
    : config_(config), install_(install), state_(state), param_(config.ToVendorParam(module)) {
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::TotalRatio() const {
    return ResolvePositiveRatio(install_.external_ratio);
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToRotorPosition(float output_position_rad) const {
    return output_position_rad * TotalRatio();
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToRotorVelocity(float output_velocity_rad_s) const {
    return output_velocity_rad_s * TotalRatio();
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToRotorLimit(float output_limit) const {
    return fabsf(output_limit) * TotalRatio();
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToOutputPosition(float rotor_position_rad) const {
    return rotor_position_rad / TotalRatio();
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToOutputVelocity(float rotor_velocity_rad_s) const {
    return rotor_velocity_rad_s / TotalRatio();
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::ToOutputTorque(float torque_current) const {
    return torque_current * MotorTraits<MotorKind::DM, Model>::kTorqueConstant * TotalRatio();
}

template <MotorModel Model>
void MotorProtocol<MotorKind::DM, Model>::ResetPositionTracker() {
    rotor_position_initialized_ = false;
    last_rotor_position_rad_ = 0.0f;
    accumulated_rotor_position_rad_ = 0.0f;
}

template <MotorModel Model>
void MotorProtocol<MotorKind::DM, Model>::SyncRotorPosition(float rotor_position_rad) {
    rotor_position_initialized_ = true;
    last_rotor_position_rad_ = rotor_position_rad;
    accumulated_rotor_position_rad_ = rotor_position_rad;
}

template <MotorModel Model>
float MotorProtocol<MotorKind::DM, Model>::AccumulateRotorPosition(float rotor_position_rad,
                                                            float rotor_velocity_rad_s) {
    if (!rotor_position_initialized_) {
        SyncRotorPosition(rotor_position_rad);
        return accumulated_rotor_position_rad_;
    }

    const float delta = WrapDmAngleDiff(rotor_position_rad - last_rotor_position_rad_);
    const float delta_limit = (fabsf(rotor_velocity_rad_s) > 0.0f)
        ? fabsf(rotor_velocity_rad_s) + kPi
        : kDefaultResyncDeltaRad;

    if (fabsf(delta) > delta_limit) {
        SyncRotorPosition(rotor_position_rad);
        return accumulated_rotor_position_rad_;
    }

    accumulated_rotor_position_rad_ += delta;
    last_rotor_position_rad_ = rotor_position_rad;
    return accumulated_rotor_position_rad_;
}

template <MotorModel Model>
bool MotorProtocol<MotorKind::DM, Model>::TryGetRotorFeedback(float& rotor_position_rad,
                                                       float& rotor_velocity_rad_s,
                                                       float& torque_current,
                                                       float& temperature_c) const {
    const MOTOR_DM_RawFeedback_t* raw = MOTOR_DM_GetRawFeedback(const_cast<MOTOR_DM_Param_t*>(&param_));
    if (raw == nullptr) {
        return false;
    }

    rotor_position_rad = UintToFloat(raw->raw_angle, kDmPositionMin, kDmPositionMax, 16);
    if (param_.reverse) {
        rotor_position_rad = -rotor_position_rad;
    }

    rotor_velocity_rad_s = UintToFloat(static_cast<uint16_t>(raw->raw_speed), kDmVelocityMin, kDmVelocityMax, 12);
    if (param_.reverse) {
        rotor_velocity_rad_s = -rotor_velocity_rad_s;
    }

    torque_current = UintToFloat(static_cast<uint16_t>(raw->raw_current), kDmTorqueMin, kDmTorqueMax, 12);
    if (param_.reverse) {
        torque_current = -torque_current;
    }

    temperature_c = static_cast<float>(raw->raw_temp);
    return true;
}

template <MotorModel Model>
void MotorProtocol<MotorKind::DM, Model>::RefreshStateCache() {
    MotorState next = state_;
    const MOTOR_t* motor = instance_ ? &instance_->motor : nullptr;
    if (motor == nullptr) {
        ResetPositionTracker();
        last_online_ = false;
        state_ = {};
        return;
    }

    next.online = motor->header.online;
    if (!next.online) {
        ResetPositionTracker();
        last_online_ = false;
        state_ = next;
        return;
    }

    float rotor_position_rad = 0.0f;
    float rotor_velocity_rad_s = 0.0f;
    float torque_current = 0.0f;
    float temperature_c = 0.0f;
    if (!TryGetRotorFeedback(rotor_position_rad, rotor_velocity_rad_s, torque_current, temperature_c)) {
        ResetPositionTracker();
        last_online_ = false;
        next.online = false;
        state_ = next;
        return;
    }

    if (!last_online_) {
        SyncRotorPosition(rotor_position_rad);
    }

    next.position_rad = ToOutputPosition(AccumulateRotorPosition(rotor_position_rad, rotor_velocity_rad_s));
    next.position_single_turn_rad = WrapToPi(next.position_rad);
    next.velocity_rad_s = ToOutputVelocity(rotor_velocity_rad_s);
    next.torque_nm = ToOutputTorque(torque_current);
    next.temperature_c = temperature_c;
    next.device_temperature_c = static_cast<float>(instance_->rotor_temp);
    next.protocol_status_code = instance_->status_raw;
    next.protocol_fault = EncodeDmFault(instance_->status);
    next.protocol_state = DecodeDmProtocolState(instance_->status);

    last_online_ = true;
    state_ = next;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::Register() {
  if (instance_ != nullptr) {
        state_.protocol_state = MotorProtocolState::Registered;
        return DEVICE_OK;
  }  
  const int8_t ret = MOTOR_DM_AttachExternal(&param_, &vendor_instance_);
    if (ret == DEVICE_OK) {
        instance_ = &vendor_instance_;
        state_.protocol_state = MotorProtocolState::Registered;
    }
    return ret;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::Enable() {
    if (instance_ != nullptr && instance_->motor.header.online && instance_->status == MOTOR_DM_STATUS_ENABLED) {
        state_.protocol_status_code = instance_->status_raw;
        state_.protocol_fault = EncodeDmFault(instance_->status);
        return DEVICE_OK;
    }
    return MOTOR_DM_Enable(&param_);
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::Disable() {
    ClearPendingCommand();
    if (instance_ != nullptr && instance_->motor.header.online && instance_->status == MOTOR_DM_STATUS_DISABLED) {
        state_.protocol_status_code = instance_->status_raw;
        state_.protocol_fault = EncodeDmFault(instance_->status);
        return DEVICE_OK;
    }
    return MOTOR_DM_Disable(&param_);
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::Relax() {
    ClearPendingCommand();
    return MOTOR_DM_Relax(&param_);
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::SetZero() {
    ClearPendingCommand();
    const int8_t ret = MOTOR_DM_SetZero(&param_);
    if (ret == DEVICE_OK) {
        ResetPositionTracker();
        state_.position_rad = 0.0f;
        state_.position_single_turn_rad = 0.0f;
        state_.last_commit_ok = true;
    } else {
        state_.last_commit_ok = false;
    }
    return ret;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::Update() {
    const int8_t ret = MOTOR_DM_Update(&param_);
    if (ret == DEVICE_OK) {
        RefreshStateCache();
    }
    return ret;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::CommitCommand() {
    int8_t ret = DEVICE_OK;
    switch (pending_type_) {
        case PendingCommandType::Velocity:
            ret = MOTOR_DM_VelCtrl(&param_, pending_velocity_);
            break;
        case PendingCommandType::Position:
            ret = MOTOR_DM_PosVelCtrl(&param_, pending_position_, pending_position_velocity_limit_);
            break;
        case PendingCommandType::Mit:
            ret = MOTOR_DM_MITCtrl(&param_, &pending_mit_output_);
            break;
        case PendingCommandType::None:
        default:
            state_.last_commit_ok = true;
            return DEVICE_OK;
    }

    debug_.last_commit_ret = ret;
    state_.last_commit_ok = (ret == DEVICE_OK);
    if (ret == DEVICE_OK) {
        ClearPendingCommand();
    }
    return ret;
}

template <MotorModel Model>
void MotorProtocol<MotorKind::DM, Model>::ClearPendingCommand() {
    pending_type_ = PendingCommandType::None;
    pending_velocity_ = 0.0f;
    pending_position_ = 0.0f;
    pending_position_velocity_limit_ = 0.0f;
    pending_mit_output_ = {};
    debug_.pending_type = pending_type_;
    debug_.pending_velocity = pending_velocity_;
    debug_.pending_position = pending_position_;
    debug_.pending_position_velocity_limit = pending_position_velocity_limit_;
    debug_.pending_mit_torque = pending_mit_output_.torque;
    state_.command_pending = false;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::SetTorque(float torque_nm) {
    constexpr float peak_torque = MotorTraits<MotorKind::DM, Model>::kPeakTorque;
    constexpr float rated_torque = MotorTraits<MotorKind::DM, Model>::kRatedTorque;
    const float max_torque_nm = (peak_torque > 0.0f) ? peak_torque : rated_torque;
    if (max_torque_nm <= 0.0f) {
        return DEVICE_ERR;
    }
    return SetMIT(0.0f, 0.0f, 0.0f, 0.0f, AbsClip(torque_nm, max_torque_nm));
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::SetVelocity(float velocity) {
    pending_velocity_ = AbsClip(ToRotorVelocity(velocity), ToRotorLimit(MotorTraits<MotorKind::DM, Model>::kMaxVelocity));
    pending_type_ = PendingCommandType::Velocity;
    debug_.pending_type = pending_type_;
    debug_.pending_velocity = pending_velocity_;
    state_.command_pending = true;
    return DEVICE_OK;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::SetPosition(float position, float max_velocity) {
    constexpr float max_velocity_limit = MotorTraits<MotorKind::DM, Model>::kMaxVelocity;
    constexpr float max_position_limit = MotorTraits<MotorKind::DM, Model>::kMaxPosition;
    const float output_velocity_limit = (max_velocity > 0.0f) ? AbsClip(max_velocity, max_velocity_limit) : max_velocity_limit;
    const float rotor_position = ToRotorPosition(position);
    const float rotor_position_limit = (max_position_limit > 0.0f) ? ToRotorLimit(max_position_limit) : 0.0f;
    pending_position_ = (rotor_position_limit > 0.0f) ? AbsClip(rotor_position, rotor_position_limit) : rotor_position;
    pending_position_velocity_limit_ = ToRotorVelocity(output_velocity_limit);
    pending_type_ = PendingCommandType::Position;
    debug_.pending_type = pending_type_;
    debug_.pending_position = pending_position_;
    debug_.pending_position_velocity_limit = pending_position_velocity_limit_;
    state_.command_pending = true;
    return DEVICE_OK;
}

template <MotorModel Model>
int8_t MotorProtocol<MotorKind::DM, Model>::SetMIT(float position, float velocity, float kp, float kd, float torque_ff) {
    constexpr float max_position_limit = MotorTraits<MotorKind::DM, Model>::kMaxPosition;
    constexpr float max_velocity_limit = MotorTraits<MotorKind::DM, Model>::kMaxVelocity;
    constexpr float peak_torque = MotorTraits<MotorKind::DM, Model>::kPeakTorque;
    const float rotor_position = ToRotorPosition(position);
    const float rotor_velocity = ToRotorVelocity(velocity);
    const float rotor_position_limit = (max_position_limit > 0.0f) ? ToRotorLimit(max_position_limit) : 0.0f;
    const float rotor_velocity_limit = ToRotorLimit(max_velocity_limit);
    pending_mit_output_.angle = (rotor_position_limit > 0.0f) ? AbsClip(rotor_position, rotor_position_limit) : rotor_position;
    pending_mit_output_.velocity = AbsClip(rotor_velocity, rotor_velocity_limit);
    pending_mit_output_.kp = kp;
    pending_mit_output_.kd = kd;
    pending_mit_output_.torque = (peak_torque > 0.0f) ? AbsClip(torque_ff, peak_torque) : torque_ff;
    pending_type_ = PendingCommandType::Mit;
    debug_.pending_type = pending_type_;
    debug_.pending_position = pending_mit_output_.angle;
    debug_.pending_velocity = pending_mit_output_.velocity;
    debug_.pending_mit_torque = pending_mit_output_.torque;
    state_.command_pending = true;
    return DEVICE_OK;
}

template <MotorModel Model>
const DmProtocolDebugSnapshot& MotorProtocol<MotorKind::DM, Model>::GetDebugSnapshot() const {
    return debug_;
}

template class MotorProtocol<MotorKind::DM, MotorModel::J10010>;
template class MotorProtocol<MotorKind::DM, MotorModel::J10010L>;
template class MotorProtocol<MotorKind::DM, MotorModel::J10422P>;
template class MotorProtocol<MotorKind::DM, MotorModel::J3507>;
template class MotorProtocol<MotorKind::DM, MotorModel::J4310>;
template class MotorProtocol<MotorKind::DM, MotorModel::J4310P>;
template class MotorProtocol<MotorKind::DM, MotorModel::J4340>;
template class MotorProtocol<MotorKind::DM, MotorModel::J4340P>;
template class MotorProtocol<MotorKind::DM, MotorModel::J6006>;
template class MotorProtocol<MotorKind::DM, MotorModel::J6248P>;
template class MotorProtocol<MotorKind::DM, MotorModel::J8006>;
template class MotorProtocol<MotorKind::DM, MotorModel::J8009>;
template class MotorProtocol<MotorKind::DM, MotorModel::J8009P>;
template class MotorProtocol<MotorKind::DM, MotorModel::H3510>;

} // namespace mr::motor
