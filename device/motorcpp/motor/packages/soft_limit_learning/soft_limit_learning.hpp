#pragma once

// SoftLimitLearning 使用说明
// ============================================================================
// 作用:
//   用电机反馈位置/速度自动学习单轴软件限位。调用者负责实际控制电机运动，
//   本类只负责观察反馈、判断是否撞到机械端点、保存并导出上下限。学习完成后，
//   推荐由 motor/controller 保存导出的上下限，并在自己的控制逻辑里执行限位保护。
//   ClampPosition() / LimitVelocity() 只是本类额外提供的便捷保护工具。
//
// 基本流程:
//   1. 创建 SoftLimitLearning 实例，并用 Configure() 配置本轴寻限速度、
//      已知行程、运行边距和最小合法行程。
//   2. 每个控制周期都调用 Observe(motor.GetState(), dt_s)。必须在电机反馈
//      Update() 之后调用，否则失速判断没有有效反馈。
//   3. 需要自动寻找下限时调用 StartSeekLower()，然后外部
//      控制器使用 GetSeekVelocity() 作为速度目标驱动电机。
//   4. 需要自动寻找上限时调用 StartSeekUpper()，同样使用
//      GetSeekVelocity() 驱动电机。
//   5. Observe() 会在满足“速度足够小 + 位置变化足够小 + 连续周期足够多”时
//      自动捕获当前端点。上下限都有效后，GetState() 会变为 Ready。
//   6. 学习完成后，可用 GetLearnedLimits() 导出学习到的上下限给 motor/controller。
//      如果调用者不想在 motor 侧实现限位，也可直接用 ClampPosition() / LimitVelocity()
//      对目标位置和速度做保护。
//   7. 若只寻到一侧端点且已知机械总行程，可调用 StartSeekLowerWithTravel()
//      或 StartSeekUpperWithTravel()，学习器会根据端点和行程自动推算完整范围。
//   8. 若需要一次完成上下限学习，可调用 StartSeekUpperThenLower()，学习器会先
//      寻上限，再自动切换到寻下限，最终得到完整范围。
//   9. 学习完成后可通过 GetPostLearnTargetPosition() 取得建议回到的位置
//      (下限/中位/上限)，调用者负责发送位置控制帧。
//
// 伪代码示例:
//   // 1) 一句构建: {寻限速度, 已知行程, 运行边距, 最小合法行程}
//   SoftLimitLearning learner({3.0f, 1.0f, 0.02f, 0.05f});
//
//   // 2) 一句启动: 根据需要选择其中一种
//   learner.StartSeekUpperThenLower();  // 先寻上限，再自动寻下限
//   // learner.StartSeekLower();        // 只寻下限
//   // learner.StartSeekUpper();        // 只寻上限
//   // learner.StartSeekLowerWithTravel(); // 寻下限 + 已知行程推算上限
//   // learner.StartSeekUpperWithTravel(); // 寻上限 + 已知行程推算下限
//
//   // 3) 控制周期: 学习器只观察反馈并给出寻限速度，controller 负责闭环控制
//   controller.Update();
//   learner.Observe(controller.GetState(), dt_s);
//   if (learner.IsSeeking()) {
//       controller.SetVelocity(learner.GetSeekVelocity());
//   }
//   controller.CommitCommand();
//
//   // 4) 学习完成后导出上下限，交给 motor/controller 保存并执行限位
//   float lower = 0.0f;
//   float upper = 0.0f;
//   if (learner.GetLearnedLimits(lower, upper)) {
//       motor.SetSoftLimits(lower, upper);  // 伪代码: 具体接口按 motor 实现替换
//   }
//
// 关键配置项:
//   seek_velocity_rad_s : 每个实例自己的寻限速度幅值，StartSeek* 内部自动决定方向。
//   known_travel_rad    : 每个实例自己的已知机械总行程，仅 WithTravel 模式使用。
//   limit_margin_rad : 每个实例自己的运行边距，使用 Clamp/LimitVelocity 时保留。
//   min_range_rad    : 每个实例自己的最小合法行程，过小会拒绝提交范围。
//   其它通用学习参数使用下方 SOFT_LIMIT_LEARNING_* 宏固定；如需修改这些策略，
//   通过编译选项覆盖宏或修改默认宏值后重新编译。
//
// 注意事项:
//   - StartSeekLower/Upper 只改变学习状态和目标寻限速度，不会直接驱动电机。
//   - seek_velocity_rad_s 配置正值即可；下限内部自动转为负速度，上限为正速度。
//   - Observe() 依赖 MotorState.online、position_rad、velocity_rad_s 有效。
//   - CancelSeek() 可取消当前寻限；ClearRange() 会清除已学习范围。
//   - CaptureLowerFromObserved()/CaptureUpperFromObserved() 可用于手动移动到端点
//     后捕获当前位置。
//   - GetLearnedLimits() 输出的是已经扣除 learned_limit_margin_rad 后的学习结果；
//     是否再额外保留运行边距，应由接收这些限位值的 motor/controller 决定。
// ============================================================================

#include <stdint.h>

#include "component/timer.hpp"
#include "device/motor/core/motor_state.hpp"

#ifndef SOFT_LIMIT_LEARNING_STALL_VELOCITY_THRESHOLD_RAD_S
#define SOFT_LIMIT_LEARNING_STALL_VELOCITY_THRESHOLD_RAD_S (0.8f)
#endif

#ifndef SOFT_LIMIT_LEARNING_STALL_POSITION_WINDOW_RAD
#define SOFT_LIMIT_LEARNING_STALL_POSITION_WINDOW_RAD (0.2f)
#endif

#ifndef SOFT_LIMIT_LEARNING_STALL_CYCLES_REQUIRED
#define SOFT_LIMIT_LEARNING_STALL_CYCLES_REQUIRED (20u)
#endif

#ifndef SOFT_LIMIT_LEARNING_SEEK_TIMEOUT_S
#define SOFT_LIMIT_LEARNING_SEEK_TIMEOUT_S (8.0f)
#endif

#ifndef SOFT_LIMIT_LEARNING_SEEK_STARTUP_IGNORE_S
#define SOFT_LIMIT_LEARNING_SEEK_STARTUP_IGNORE_S (0.15f)
#endif

#ifndef SOFT_LIMIT_LEARNING_LEARNED_LIMIT_MARGIN_RAD
#define SOFT_LIMIT_LEARNING_LEARNED_LIMIT_MARGIN_RAD (0.03f)
#endif

namespace mr::motor {

struct SoftLimitRange {
    bool lower_valid = false;
    bool upper_valid = false;
    float lower_rad = 0.0f;
    float upper_rad = 0.0f;
};

struct SoftLimitLearningConfig {
    float seek_velocity_rad_s = 0.0f;
    float known_travel_rad = 0.0f;
    float limit_margin_rad = 0.0f;
    float min_range_rad = 0.0f;
};

enum class SoftLimitReturnTarget : uint8_t {
    None = 0,
    Lower,
    Center,
    Upper,
};

enum class SoftLimitLearningWorkflow : uint8_t {
    None = 0,
    SingleLower,
    SingleUpper,
    LowerWithTravel,
    UpperWithTravel,
    UpperThenLower,
    LowerThenUpper,
};

enum class SoftLimitLearningState : uint8_t {
    Idle = 0,
    SeekingLower,
    SeekingUpper,
    Ready,
    Failed,
};

class SoftLimitLearning final {
public:
    SoftLimitLearning();
    explicit SoftLimitLearning(const SoftLimitLearningConfig& config);

    void Configure(const SoftLimitLearningConfig& config);
    const SoftLimitLearningConfig& GetConfig() const;

    void Reset();
    void ResetLearningState();
    void ClearRange();

    void Observe(const MotorState& state);
    void Observe(const MotorState& state, float dt_s);
    void ResetObserverTimer();

    bool StartSeekLower();
    bool StartSeekUpper();
    bool StartSeekLowerWithTravel();
    bool StartSeekUpperWithTravel();
    bool StartSeekUpperThenLower();
    bool StartSeekLowerThenUpper();
    void CancelSeek();
    void MarkFailed();

    bool CaptureLower(float position_rad);
    bool CaptureUpper(float position_rad);
    bool CaptureLowerFromObserved();
    bool CaptureUpperFromObserved();
    bool SetRange(float lower_rad, float upper_rad);
    bool SetRangeByLowerAndTravel(float lower_rad, float travel_rad);
    bool SetRangeByUpperAndTravel(float upper_rad, float travel_rad);

    bool HasObservedState() const;
    const MotorState& GetObservedState() const;

    bool HasLower() const;
    bool HasUpper() const;
    bool HasRange() const;
    bool IsSeeking() const;
    bool IsReady() const;
    bool IsFailed() const;

    float GetTravelRad() const;
    float GetCenterRad() const;
    float ClampPosition(float position_rad) const;
    float ClampPosition(float position_rad, float margin_rad) const;
    float LimitVelocity(float position_rad, float velocity_rad_s) const;
    float LimitVelocity(float position_rad, float velocity_rad_s, float margin_rad) const;
    bool IsPositionWithinRange(float position_rad) const;
    bool IsPositionWithinRange(float position_rad, float margin_rad) const;
    bool IsAtLowerLimit(float position_rad) const;
    bool IsAtLowerLimit(float position_rad, float margin_rad) const;
    bool IsAtUpperLimit(float position_rad) const;
    bool IsAtUpperLimit(float position_rad, float margin_rad) const;

    const SoftLimitRange& GetRange() const;
    bool GetLearnedLowerLimit(float& lower_rad) const;
    bool GetLearnedUpperLimit(float& upper_rad) const;
    bool GetLearnedLimits(float& lower_rad, float& upper_rad) const;
    SoftLimitLearningState GetState() const;
    float GetSeekVelocity() const;
    SoftLimitLearningWorkflow GetWorkflow() const;
    void SetPostLearnReturnTarget(SoftLimitReturnTarget target);
    SoftLimitReturnTarget GetPostLearnReturnTarget() const;
    bool HasPostLearnTargetPosition() const;
    float GetPostLearnTargetPosition() const;
    float GetPendingTravelRad() const;
    uint16_t GetStallCycles() const;
    float GetElapsedSeekS() const;
    float GetStartupIgnoreLeftS() const;

private:
    bool StartSeek(float seek_velocity_rad_s, bool upper, SoftLimitLearningWorkflow workflow, float travel_rad);
    bool CommitRange(SoftLimitRange range);
    void FinishSeekAt(float position_rad);
    void ResetSeekTracking();
    void ClearWorkflow();
    bool CompleteSingleSideWithTravel(float position_rad, bool upper_side);
    bool ContinueSequenceAfterFirstSide(bool captured_upper, float captured_position_rad);
    SoftLimitLearningState ResolveIdleState() const;
    float ResolveMargin(float margin_rad) const;

    SoftLimitLearningConfig config_ {};
    SoftLimitRange range_ {};
    SoftLimitLearningState state_ = SoftLimitLearningState::Idle;
    mr::comp::timer observe_timer_ {};
    MotorState observed_state_ {};
    bool has_observed_state_ = false;
    float seek_velocity_rad_s_ = 0.0f;
    float last_seek_position_rad_ = 0.0f;
    bool seek_position_initialized_ = false;
    uint16_t stall_cycles_ = 0u;
    float elapsed_seek_s_ = 0.0f;
    float startup_ignore_left_s_ = 0.0f;
    SoftLimitLearningWorkflow workflow_ = SoftLimitLearningWorkflow::None;
    SoftLimitReturnTarget post_learn_return_target_ = SoftLimitReturnTarget::None;
    float pending_travel_rad_ = 0.0f;
    float pending_seek_speed_rad_s_ = 0.0f;
    bool post_learn_target_available_ = false;
    float post_learn_target_position_rad_ = 0.0f;
};

} // namespace mr::motor
