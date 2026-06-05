#pragma once

// 电机控制器封装层。
//
// 构建方式:
//   1. 默认参数: MotorControllerT<RmM2006Motor> controller(motor);
//      默认参数来自 motor_controller_defaults.hpp 中的 MotorControllerDefaults<MotorType> 特化。
//   2. 自定义参数: MotorControllerT<RmM2006Motor> controller(motor, config);
//      config 中的 PID 指针必须指向生命周期长于 controller 的静态/全局/外部对象。
//
// 推荐使用流程:
//   controller.Initialize();                    // Register + Enable
//   controller.Step([](auto& ctrl) {            // 周期调用: Update -> 设置命令 -> Commit
//       ctrl.SetPosition(target_rad);
//   });
//
// 精细控制流程仍然保留:
//   controller.Update();                        // 先刷新反馈和控制律
//   ...                                         // 可插入限位学习、状态观测、调试逻辑
//   controller.SetVelocity(target_rad_s);        // 选择本周期目标
//   controller.CommitCommand();                  // 周期末提交到底层电机协议
//
// 控制策略: 底层电机支持原生速度/位置/MIT 时优先透传；不支持时回退到软件 PID。

#include <stdint.h>

#include "component/controller/pid.hpp"
#include "component/pid.h"
#include "component/timer.hpp"
#include "device/motor/core/motor_install_spec.hpp"
#include "device/motor/motor.hpp"

namespace mr::motor {

struct MotorControllerConfig {
    // 速度环 PID。用于模拟速度、模拟位置的内环；nullptr 表示不可用。
    const KPID_Params_t* velocity_pid;
    // 位置环 PID。用于模拟位置或位置到力矩；nullptr 表示不可用。
    const KPID_Params_t* position_pid;
    // 控制器采样频率 Hz。<=0 时回退到 PID 库默认频率。
    float sample_freq;

    // 反馈位置和速度的一阶低通截止频率 Hz。<=0 时禁用反馈滤波。
    float feedback_lowpass_cutoff_hz;
    // 输出力矩的一阶低通截止频率 Hz。<=0 时禁用输出滤波。
    float output_lowpass_cutoff_hz;

        constexpr MotorControllerConfig()
                : velocity_pid(nullptr),
                    position_pid(nullptr),
                    sample_freq(0.0f),
                    feedback_lowpass_cutoff_hz(0.0f),
                    output_lowpass_cutoff_hz(0.0f) {}

        constexpr MotorControllerConfig(const KPID_Params_t* velocity,
                                                                        const KPID_Params_t* position,
                                                                        float sample,
                                                                        float feedback_cutoff,
                                                                        float output_cutoff)
                : velocity_pid(velocity),
                    position_pid(position),
                    sample_freq(sample),
                    feedback_lowpass_cutoff_hz(feedback_cutoff),
                    output_lowpass_cutoff_hz(output_cutoff) {}

        constexpr MotorControllerConfig(const KPID_Params_t* velocity,
                                                                        const KPID_Params_t* position,
                                                                        float sample,
                                                                        float,
                                                                        float,
                                                                        float feedback_cutoff,
                                                                        float output_cutoff)
                : MotorControllerConfig(velocity, position, sample, feedback_cutoff,
                                                                output_cutoff) {}
};

template <typename MotorType>
struct MotorControllerDefaults {
    static constexpr MotorControllerConfig Config() {
        return {nullptr, nullptr, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    }
};

} // namespace mr::motor

#include "device/motor/packages/controller/motor_controller_defaults.hpp"

namespace mr::motor {

template <typename MotorType>
class MotorControllerT final {
public:
    explicit MotorControllerT(MotorType& motor);
    MotorControllerT(MotorType& motor, const MotorControllerConfig& config);

    int8_t Initialize();
    int8_t Tick();

    template <typename CommandFn>
    int8_t Step(CommandFn command_fn) {
        const int8_t update_ret = Update();
        if (update_ret != DEVICE_OK) {
            return update_ret;
        }

        const int8_t command_ret = command_fn(*this);
        if (command_ret != DEVICE_OK) {
            return command_ret;
        }

        return CommitCommand();
    }

    int8_t Register();
    int8_t Enable();
    int8_t Disable();
    int8_t Relax();
    int8_t Update();
    int8_t UpdateFeedback();
    int8_t UpdateCommand();
    int8_t CommitCommand();
    bool HasPendingCommand() const;
    void ClearPendingCommand();

    int8_t SetTorque(float torque_nm);
    int8_t SetVelocity(float velocity);
    int8_t SetPosition(float position, float max_velocity = 0.0f);
    int8_t SetPositionTorque(float position, float torque_limit = 0.0f);
    int8_t SetMIT(float position, float velocity, float kp, float kd, float torque_ff);

    MotorState GetState() const;
    const MotorInstallSpec& GetInstallConfig() const;
    const MotorType& GetMotor() const;
    float GetLastFeedbackPosition() const;
    float GetLastFeedbackVelocity() const;
    float GetLastOutputTorque() const;
    float CalculatePositionOutput(float target, float feedback, float dt_s);
    float CalculateVelocityOutput(float target, float feedback, float dt_s);
    int8_t ResetControllers();

private:
    enum class ControlMode : uint8_t {
        Torque = 0,
        NativeVelocity,
        EmulatedVelocity,
        NativePosition,
        EmulatedPosition,
        EmulatedPositionTorque,
        NativeMit,
        EmulatedMit,
    };

    float UpdateControlDt();
    int8_t UpdateCommandFromState(const MotorState& state, float dt_s);
    float LowpassAlpha(float cutoff_hz, float dt_s) const;
    void ResetFiltersToState();
    MotorState FilterFeedback(const MotorState& state, float dt_s);
    float FilterOutputTorque(float torque_nm, float dt_s);

    MotorType& motor_;
    MotorControllerConfig config_;

    mr::comp::cntlr::pid velocity_pid_;
    mr::comp::cntlr::pid position_pid_;
    mr::comp::timer control_timer_;
    float control_dt_fallback_s_;
    bool velocity_pid_ready_;
    bool position_pid_ready_;
    float feedback_lowpass_cutoff_hz_;
    float output_lowpass_cutoff_hz_;
    bool feedback_filter_initialized_;
    bool output_filter_initialized_;
    float filtered_position_;
    float filtered_velocity_;
    float filtered_output_torque_;

    ControlMode mode_;
    float target_torque_;
    float target_velocity_;
    float target_position_;
    float target_mit_kp_;
    float target_mit_kd_;
    float target_mit_torque_ff_;
    float last_control_dt_s_;
    float last_feedback_position_;
    float last_feedback_velocity_;
    float last_output_torque_;
};

using MotorController = MotorControllerT<mr::motor::RmM3508Motor>;

} // namespace mr::motor
