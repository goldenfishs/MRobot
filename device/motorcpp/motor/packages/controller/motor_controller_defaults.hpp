#pragma once

// MotorControllerT per-model default parameters.
// Include this through motor_controller.hpp so MotorControllerConfig and the
// primary MotorControllerDefaults template are already declared.

namespace mr::motor {

template <>
struct MotorControllerDefaults<RmM2006Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.3f,
        1.25f,
        0.02f,
        0.008f,
        0.35f,
        RmM2006Motor::Traits::kMaxTorque,
        100.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        1.0f,
        60.0f,
        0.0f,
        0.0f,
        0.0f,
        RmM2006Motor::Traits::kMaxVelocity,
        80.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            500.0f,
            RmM2006Motor::Traits::kMaxVelocity,
            RmM2006Motor::Traits::kMaxTorque,
            160.0f,
            120.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<RmM3508Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<RmM6020Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ10010Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ10010LMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ10422PMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ3507Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ4310Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ4310PMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ4340Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ4340PMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ6006Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ6248PMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ8006Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ8009Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmJ8009PMotor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<DmH3510Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso0Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso1Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso2Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso3Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso4Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso5Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

template <>
struct MotorControllerDefaults<LzRso6Motor> {
    static inline constexpr KPID_Params_t kVelocityPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static inline constexpr KPID_Params_t kPositionPid{
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
        0.0f,
    };

    static constexpr MotorControllerConfig Config() {
        return {
            &kVelocityPid,
            &kPositionPid,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
        };
    }
};

} // namespace mr::motor