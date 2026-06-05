#pragma once

// 强类型电机对象封装。
// 对外提供统一的 Register / Enable / Update / SetXXX 接口，内部委托给对应 Protocol。

#include <type_traits>

#include "component/math/scalar.hpp"
#include "device/device.h"
#include "device/motor.h"
#include "device/motor/core/motor_instance_config.hpp"
#include "device/motor/core/motor_install_spec.hpp"
#include "device/motor/core/motor_kind.hpp"
#include "device/motor/core/motor_model.hpp"
#include "device/motor/core/motor_state.hpp"
#include "device/motor/core/motor_traits.hpp"
#include "device/motor/protocol/dm_protocol.hpp"
#include "device/motor/protocol/lz_protocol.hpp"
#include "device/motor/protocol/rm_protocol.hpp"

namespace mr::motor {

template <MotorKind Kind, MotorModel Model>
class MotorT final {
public:
    static_assert(MotorModelValidV<Kind, Model>, "Invalid motor kind/model combination");

    using Traits = MotorTraits<Kind, Model>;
    using Config = MotorInstanceConfig<Kind>;
    using Protocol = MotorProtocol<Kind, Model>;

    explicit MotorT(const Config& config,
                    const MotorInstallSpec& install = kDirectDriveInstall,
                    const MotorTemperatureProtectionConfig& temperature_protection = {})
        : config_(config),
          install_(install),
          temperature_protection_(NormalizeTemperatureProtection(temperature_protection)),
          state_{},
          protocol_(config, install_, state_, Traits::kVendorModule) {
        UpdateTemperatureProtectionFlags();
    }

    int8_t Register() { return protocol_.Register(); }
    int8_t Enable() {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        return protocol_.Enable();
    }
    int8_t Disable() { return protocol_.Disable(); }
    int8_t Relax() { return protocol_.Relax(); }
    int8_t SetZero() {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        if constexpr (Traits::kHasNativeZeroSet) {
            return protocol_.SetZero();
        } else {
            return DEVICE_ERR_UNSUPPORTED;
        }
    }
    int8_t Update() {
        const int8_t ret = protocol_.Update();
        UpdateTemperatureProtectionFlags();
        if (ret == DEVICE_OK && state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        return ret;
    }
    int8_t CommitCommand() {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        int8_t ret = protocol_.CommitCommand();
        state_.command_pending = protocol_.HasPendingCommand();
        return ret;
    }
    bool HasPendingCommand() const { return state_.command_pending; }
    void ClearPendingCommand() {
        protocol_.ClearPendingCommand();
        state_.command_pending = false;
    }
    const auto& ProtocolDebug() const { return protocol_.GetDebugSnapshot(); }

    void SetTemperatureProtection(const MotorTemperatureProtectionConfig& config) {
        temperature_protection_ = NormalizeTemperatureProtection(config);
        UpdateTemperatureProtectionFlags();
    }
    void SetTemperatureThresholds(float warning_c,
                                  float limit_c,
                                  bool auto_relax_on_limit = true) {
        SetTemperatureProtection({warning_c, limit_c, auto_relax_on_limit});
    }
    void DisableTemperatureProtection() {
        temperature_protection_ = {};
        UpdateTemperatureProtectionFlags();
    }
    void ClearTemperatureLimitLatch() {
        state_.temperature_limit_latched = false;
        UpdateTemperatureProtectionFlags();
    }
    MotorTemperatureProtectionConfig GetTemperatureProtectionConfig() const {
        return temperature_protection_;
    }
    bool IsTemperatureLimitActive() const { return state_.temperature_limit_latched; }

    int8_t SetTorque(float torque_nm) {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        if constexpr (Traits::kSupportsTorque) {
            return protocol_.SetTorque(torque_nm);
        } else {
            return DEVICE_ERR_UNSUPPORTED;
        }
    }

    int8_t SetVelocity(float velocity) {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        if constexpr (Traits::kSupportsVelocity) {
            return protocol_.SetVelocity(velocity);
        } else {
            return DEVICE_ERR_UNSUPPORTED;
        }
    }

    int8_t SetPosition(float position, float max_velocity = 0.0f) {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        if constexpr (Traits::kSupportsPosition) {
            return protocol_.SetPosition(position, max_velocity);
        } else {
            return DEVICE_ERR_UNSUPPORTED;
        }
    }

    int8_t SetMIT(float position, float velocity, float kp, float kd, float torque_ff) {
        UpdateTemperatureProtectionFlags();
        if (state_.temperature_limit_latched) {
            return HoldForTemperatureLimit();
        }
        if constexpr (Traits::kSupportsMit) {
            return protocol_.SetMIT(position, velocity, kp, kd, torque_ff);
        } else {
            return DEVICE_ERR_UNSUPPORTED;
        }
    }

    MotorState GetState() const { return state_; }
    const MotorInstallSpec& GetInstallConfig() const { return install_; }

    static constexpr MotorKind kind() { return Kind; }
    static constexpr MotorModel model() { return Model; }
    static constexpr const char* name() { return Traits::kName; }
    static constexpr float gear_ratio() { return Traits::kGearRatio; }
    static constexpr float max_position() { return Traits::kMaxPosition; }
    static constexpr float max_velocity() { return Traits::kMaxVelocity; }
    static constexpr float recommended_velocity() { return Traits::kRecommendedVelocity; }
    static constexpr float rated_velocity() { return Traits::kRatedVelocity; }
    static constexpr float recommended_current() { return Traits::kRecommendedCurrent; }
    static constexpr float rated_current() { return Traits::kRatedCurrent; }
    static constexpr float peak_current() { return Traits::kPeakCurrent; }
    static constexpr float torque_constant() { return Traits::kTorqueConstant; }
    static constexpr float rated_torque() { return Traits::kRatedTorque; }
    static constexpr float peak_torque() { return Traits::kPeakTorque; }
    static constexpr MotorCapability capabilities() { return Traits::kCapabilities; }

private:
    static bool TemperatureThresholdEnabled(float threshold_c) {
        return mr::component::math::is_finite_scalar(threshold_c) &&
               threshold_c > 0.0f;
    }

    static MotorTemperatureProtectionConfig NormalizeTemperatureProtection(
        const MotorTemperatureProtectionConfig& config) {
        MotorTemperatureProtectionConfig normalized = config;
        if (!TemperatureThresholdEnabled(normalized.warning_c)) {
            normalized.warning_c = kMotorDefaultTemperatureProtection.warning_c;
        }
        if (!TemperatureThresholdEnabled(normalized.limit_c)) {
            normalized.limit_c = kMotorDefaultTemperatureProtection.limit_c;
        }
        normalized.warning_c =
            TemperatureThresholdEnabled(normalized.warning_c) ? normalized.warning_c : 0.0f;
        normalized.limit_c =
            TemperatureThresholdEnabled(normalized.limit_c) ? normalized.limit_c : 0.0f;
        if (normalized.warning_c > 0.0f && normalized.limit_c > 0.0f &&
            normalized.warning_c > normalized.limit_c) {
            normalized.warning_c = normalized.limit_c;
        }
        return normalized;
    }

    void UpdateTemperatureProtectionFlags() {
        state_.temperature_warning_threshold_c = temperature_protection_.warning_c;
        state_.temperature_limit_threshold_c = temperature_protection_.limit_c;

        const bool primary_temperature_valid =
            mr::component::math::is_finite_scalar(state_.temperature_c);
        const bool device_temperature_valid =
            mr::component::math::is_finite_scalar(state_.device_temperature_c);
        float protection_temperature_c =
            primary_temperature_valid ? state_.temperature_c : 0.0f;
        if (device_temperature_valid &&
            (!primary_temperature_valid ||
             state_.device_temperature_c > protection_temperature_c)) {
            protection_temperature_c = state_.device_temperature_c;
        }
        const bool valid_temperature =
            primary_temperature_valid || device_temperature_valid;
        state_.temperature_warning =
            valid_temperature &&
            TemperatureThresholdEnabled(temperature_protection_.warning_c) &&
            protection_temperature_c >= temperature_protection_.warning_c;
        state_.temperature_over_limit =
            valid_temperature &&
            TemperatureThresholdEnabled(temperature_protection_.limit_c) &&
            protection_temperature_c >= temperature_protection_.limit_c;

        if (!TemperatureThresholdEnabled(temperature_protection_.limit_c)) {
            state_.temperature_limit_latched = false;
        } else if (state_.temperature_over_limit) {
            state_.temperature_limit_latched = true;
        }
    }

    int8_t HoldForTemperatureLimit() {
        ClearPendingCommand();
        if (!temperature_protection_.auto_relax_on_limit) {
            return DEVICE_ERR;
        }
        return protocol_.Relax();
    }

    Config config_;
    MotorInstallSpec install_;
    MotorTemperatureProtectionConfig temperature_protection_;
    MotorState state_{};
    Protocol protocol_;
};

} // namespace mr::motor
