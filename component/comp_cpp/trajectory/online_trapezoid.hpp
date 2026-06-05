#pragma once

#include <math.h>

#include "component/trajectory/trajectory_types.hpp"

namespace mr::comp::traj {

struct OnlineTrapezoidAxisConfig {
  Scalar max_velocity = 0.0f;
  Scalar max_acceleration = 0.0f;
  Scalar position_epsilon = 0.002f;
  Scalar velocity_epsilon_floor = 0.02f;
};

struct OnlineTrapezoidAxisSample {
  Scalar position = 0.0f;
  Scalar velocity = 0.0f;
  bool valid = false;
  bool reached = false;
};

inline OnlineTrapezoidAxisSample update_trapezoid_axis(
    Scalar current,
    Scalar target,
    Scalar* velocity,
    Scalar max_velocity,
    Scalar max_acceleration,
    Scalar dt,
    Scalar position_epsilon = 0.002f,
    Scalar velocity_epsilon_floor = 0.02f) {
  OnlineTrapezoidAxisSample out{};
  out.position = current;
  if (velocity == nullptr || !is_finite_scalar(current) ||
      !is_finite_scalar(target)) {
    return out;
  }

  Scalar max_vel = abs_scalar(max_velocity);
  Scalar max_acc = abs_scalar(max_acceleration);
  if (!is_finite_scalar(*velocity)) {
    *velocity = 0.0f;
  }
  dt = mr::component::math::sanitize_dt(
      dt, 0.0f, mr::component::math::kDefaultEpsilon,
      mr::component::math::kFiniteLimit);
  position_epsilon = abs_scalar(position_epsilon);
  velocity_epsilon_floor = abs_scalar(velocity_epsilon_floor);

  if (!is_finite_scalar(max_vel) || !is_finite_scalar(max_acc) ||
      max_vel <= kDefaultEpsilon || max_acc <= kDefaultEpsilon) {
    out.velocity = *velocity;
    return out;
  }

  const Scalar error = target - current;
  const Scalar stop_vel_epsilon =
      fmaxf(velocity_epsilon_floor, max_acc * dt);

  if (abs_scalar(error) <= position_epsilon &&
      abs_scalar(*velocity) <= stop_vel_epsilon) {
    *velocity = 0.0f;
    out.position = target;
    out.velocity = 0.0f;
    out.valid = true;
    out.reached = true;
    return out;
  }

  const Scalar brake_velocity =
      sqrtf(fmaxf(0.0f, 2.0f * max_acc * abs_scalar(error)));
  Scalar desired_velocity = copysignf(fminf(max_vel, brake_velocity), error);
  if (brake_velocity < stop_vel_epsilon) {
    desired_velocity = 0.0f;
  }

  const Scalar max_delta_velocity = max_acc * dt;
  *velocity = mr::component::math::apply_delta_limit(
      desired_velocity, *velocity, max_delta_velocity);
  *velocity = mr::component::math::abs_clip_scalar(*velocity, max_vel);

  if (abs_scalar(error) <= position_epsilon &&
      abs_scalar(*velocity) <= stop_vel_epsilon) {
    *velocity = 0.0f;
    out.position = target;
    out.velocity = 0.0f;
    out.valid = true;
    out.reached = true;
    return out;
  }

  out.position = current + (*velocity) * dt;
  out.velocity = *velocity;
  out.valid = is_finite_scalar(out.position) && is_finite_scalar(out.velocity);
  out.reached = false;
  return out;
}

class OnlineTrapezoidAxis {
 public:
  OnlineTrapezoidAxis() = default;

  explicit OnlineTrapezoidAxis(const OnlineTrapezoidAxisConfig& config)
      : config_(config) {}

  void Configure(const OnlineTrapezoidAxisConfig& config) {
    config_ = config;
  }

  void Reset(Scalar velocity = 0.0f) {
    velocity_ = velocity;
  }

  OnlineTrapezoidAxisSample Update(Scalar current,
                                   Scalar target,
                                   Scalar dt) {
    return update_trapezoid_axis(
        current, target, &velocity_, config_.max_velocity,
        config_.max_acceleration, dt, config_.position_epsilon,
        config_.velocity_epsilon_floor);
  }

  Scalar velocity() const { return velocity_; }
  const OnlineTrapezoidAxisConfig& config() const { return config_; }

 private:
  OnlineTrapezoidAxisConfig config_{};
  Scalar velocity_ = 0.0f;
};

}  // namespace mr::comp::traj
