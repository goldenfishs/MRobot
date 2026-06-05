#pragma once

/*
 * 模型预测速度控制器。
 *
 * 基于位置误差和速度误差的双环速度控制器：
 *   target_velocity = kp_position * pos_error
 *   target_velocity = clamp(target_velocity, +/-velocity_limit)
 *   target_velocity = velocity_slew_limiter.update(target_velocity)
 *   output = kp_velocity * (target_velocity - velocity)
 *   output = clamp(output, +/-output_limit)
 *
 * 特性：
 *   - 双环串级控制：位置环 -> 速度环
 *   - 内置速度限幅和加速度斜率限制
 *   - 适用于点到点运动跟踪
 *
 * 使用示例：
 *   auto mpc = mr::comp::cntlr::mpc::Build(
 *       2.0f,    // kp_position: 位置环增益
 *       10.0f,   // kp_velocity: 速度环增益
 *       1.0f,    // velocity_limit: 最大速度 (m/s 或 rad/s)
 *       5.0f,    // acceleration_limit: 最大加速度 (m/s^2)
 *       3.0f     // output_limit: 力矩/力输出限幅
 *   );
 *
 *   float torque = mpc.Update(target_pos, current_pos, current_vel, dt_s);
 */

#include "component/controller/controller_types.hpp"

namespace mr::comp::cntlr {

struct mpc_config {
  Scalar kp_position = 0.0f;
  Scalar kp_velocity = 0.0f;
  SymmetricLimit velocity_limit{};
  SymmetricLimit acceleration_limit{};
  SymmetricLimit output_limit{};
};

struct mpc_step {
  Scalar target_velocity = 0.0f;
  Scalar output = 0.0f;
  bool valid = false;
};

class mpc {
 public:
  using Config = mpc_config;
  using Step = mpc_step;

  static mpc Build(const Config& config) {
    return mpc(config);
  }

  static mpc Build(Scalar kp_position,
                   Scalar kp_velocity,
                   Scalar velocity_limit = kUnlimited,
                   Scalar acceleration_limit = kUnlimited,
                   Scalar output_limit = kUnlimited) {
    Config config{};
    config.kp_position = kp_position;
    config.kp_velocity = kp_velocity;
    config.velocity_limit = SymmetricLimit::Abs(velocity_limit);
    config.acceleration_limit = SymmetricLimit::Abs(acceleration_limit);
    config.output_limit = SymmetricLimit::Abs(output_limit);
    return mpc(config);
  }

  constexpr mpc() = default;
  explicit mpc(const Config& config)
      : config_(config),
        velocity_limiter_(SlewRateLimiter::Build(config.acceleration_limit.value)) {}

  void Configure(const Config& config) {
    config_ = config;
    velocity_limiter_ = SlewRateLimiter::Build(config.acceleration_limit.value);
    last_ = {};
  }

  void Reset(Scalar current_velocity = 0.0f) {
    velocity_limiter_.Reset(current_velocity);
    last_ = {};
  }

  Scalar Update(Scalar target_position,
                Scalar position,
                Scalar velocity,
                Scalar dt_s) {
    return StepOnce(target_position, position, velocity, dt_s).output;
  }

  Step StepOnce(Scalar target_position,
                Scalar position,
                Scalar velocity,
                Scalar dt_s) {
    last_ = {};
    if (!IsUsableScalar(target_position) || !IsUsableScalar(position) ||
        !IsUsableScalar(velocity)) {
      return last_;
    }

    const Scalar pos_error = target_position - position;
    Scalar target_velocity = config_.kp_position * pos_error;
    target_velocity = config_.velocity_limit.Apply(target_velocity);
    target_velocity = velocity_limiter_.Update(target_velocity, dt_s);

    Scalar output = config_.kp_velocity * (target_velocity - velocity);
    output = config_.output_limit.Apply(output);

    last_.target_velocity = target_velocity;
    last_.output = output;
    last_.valid = true;
    return last_;
  }

  const Step& last() const { return last_; }

 private:
  Config config_{};
  SlewRateLimiter velocity_limiter_{};
  Step last_{};
};

}  // namespace mr::comp::cntlr
