#pragma once

/*
 * 梯形速度曲线规划器。
 *
 * 控制律（三段式）：
 *   Phase 1 (0 <= t < t_acc): 匀加速
 *     acceleration = a
 *     velocity = a * t
 *     position = 0.5 * a * t^2
 *
 *   Phase 2 (t_acc <= t < t_acc + t_cruise): 匀速
 *     acceleration = 0
 *     velocity = v_peak
 *     position = 0.5 * a * t_acc^2 + v_peak * (t - t_acc)
 *
 *   Phase 3 (t >= t_acc + t_cruise): 匀减速
 *     acceleration = -a
 *     velocity = v_peak - a * (t - t_acc - t_cruise)
 *     position = d_acc + v_peak * (t - t_acc) - 0.5 * a * (t - t_acc)^2
 *
 * 适用于：
 *   - 单轴位置运动规划
 *   - 梯形加减速曲线：匀加速 -> 匀速 -> 匀减速
 *   - 速度约束、加速约束下的最短时间轨迹
 *
 * 使用示例：
 *   // 初始化：配置规划器
 *   auto planner = mr::comp::traj::TrapezoidProfile();
 *   planner.configure(distance, max_velocity, max_acceleration);
 *   float start_time = get_current_time();
 *
 *   // 控制循环中（每周期执行）：
 *   float elapsed = get_current_time() - start_time;
 *   auto sample = planner.sample(elapsed);
 *   // sample.position, sample.velocity, sample.acceleration
 */

#include <math.h>

#include "trajectory_types.hpp"

namespace mr::comp::traj {

class TrapezoidProfile {
 public:
  TrapezoidProfile()
      : distance_(0.0f),
        direction_(1.0f),
        abs_distance_(0.0f),
        peak_velocity_(0.0f),
        acceleration_(0.0f),
        accel_time_(0.0f),
        cruise_time_(0.0f),
        duration_(0.0f),
        epsilon_(kDefaultEpsilon),
        valid_(false) {}

  static Scalar min_duration(Scalar distance,
                             Scalar max_velocity,
                             Scalar max_acceleration,
                             Scalar epsilon = kDefaultEpsilon) {
    const Scalar d = abs_scalar(distance);
    const Scalar v = abs_scalar(max_velocity);
    const Scalar a = abs_scalar(max_acceleration);
    if (d <= epsilon) {
      return 0.0f;
    }
    if (v <= epsilon || a <= epsilon ||
        !is_finite_scalar(d) || !is_finite_scalar(v) ||
        !is_finite_scalar(a)) {
      return -1.0f;
    }

    const Scalar t_acc = v / a;
    const Scalar accel_decel_distance = (v * v) / a;
    if (d <= accel_decel_distance) {
      return 2.0f * sqrtf(d / a);
    }
    return 2.0f * t_acc + (d - accel_decel_distance) / v;
  }

  bool configure(Scalar distance,
                 Scalar max_velocity,
                 Scalar max_acceleration,
                 Scalar epsilon = kDefaultEpsilon) {
    const Scalar duration =
        min_duration(distance, max_velocity, max_acceleration, epsilon);
    if (duration < 0.0f) {
      reset();
      return false;
    }
    return configure_synchronized(distance, max_velocity, max_acceleration,
                                  duration, epsilon);
  }

  bool configure_synchronized(Scalar distance,
                              Scalar max_velocity,
                              Scalar max_acceleration,
                              Scalar duration,
                              Scalar epsilon = kDefaultEpsilon) {
    reset();
    if (!is_finite_scalar(distance) || !is_finite_scalar(max_velocity) ||
        !is_finite_scalar(max_acceleration) || !is_finite_scalar(duration) ||
        duration < 0.0f) {
      return false;
    }

    distance_ = distance;
    abs_distance_ = abs_scalar(distance);
    direction_ = (distance >= 0.0f) ? 1.0f : -1.0f;
    duration_ = duration;
    epsilon_ = epsilon;

    if (abs_distance_ <= epsilon) {
      valid_ = true;
      return true;
    }
    if (duration_ <= epsilon) {
      return false;
    }

    const Scalar max_acc = abs_scalar(max_acceleration);
    const Scalar max_vel = abs_scalar(max_velocity);
    if (max_acc <= epsilon || max_vel <= epsilon) {
      return false;
    }

    const Scalar min_time =
        min_duration(distance, max_velocity, max_acceleration, epsilon);
    if (min_time < 0.0f || duration_ + 1.0e-5f < min_time) {
      return false;
    }

    Scalar discriminant =
        duration_ * duration_ - 4.0f * abs_distance_ / max_acc;
    if (discriminant < 0.0f) {
      if (discriminant < -1.0e-5f) {
        return false;
      }
      discriminant = 0.0f;
    }

    Scalar ta = 0.5f * (duration_ - sqrtf(discriminant));
    ta = clamp_scalar(ta, 0.0f, 0.5f * duration_);
    Scalar v_peak = max_acc * ta;

    if (v_peak > max_vel + 1.0e-4f) {
      v_peak = max_vel;
      ta = v_peak / max_acc;
    }

    const Scalar tc = duration_ - 2.0f * ta;
    accel_time_ = ta;
    cruise_time_ = (tc > 0.0f) ? tc : 0.0f;
    peak_velocity_ = v_peak;
    acceleration_ = (ta > epsilon) ? max_acc : 0.0f;
    valid_ = true;
    return true;
  }

  ScalarMotionSample sample(Scalar elapsed) const {
    ScalarMotionSample out;
    if (!valid_) {
      return out;
    }

    out.valid = true;
    if (duration_ <= epsilon_) {
      out.position = distance_;
      out.finished = true;
      return out;
    }

    const Scalar t = clamp_scalar(elapsed, 0.0f, duration_);
    out.finished = (elapsed >= duration_);

    Scalar pos_abs = abs_distance_;
    Scalar vel_abs = 0.0f;
    Scalar acc_abs = 0.0f;

    if (abs_distance_ <= epsilon_ || acceleration_ <= epsilon_) {
      pos_abs = abs_distance_;
    } else if (t <= accel_time_) {
      pos_abs = 0.5f * acceleration_ * t * t;
      vel_abs = acceleration_ * t;
      acc_abs = acceleration_;
    } else if (t <= accel_time_ + cruise_time_) {
      const Scalar cruise_t = t - accel_time_;
      pos_abs = 0.5f * acceleration_ * accel_time_ * accel_time_ +
                peak_velocity_ * cruise_t;
      vel_abs = peak_velocity_;
    } else if (t < duration_) {
      const Scalar decel_t = t - accel_time_ - cruise_time_;
      const Scalar before_decel =
          0.5f * acceleration_ * accel_time_ * accel_time_ +
          peak_velocity_ * cruise_time_;
      pos_abs = before_decel + peak_velocity_ * decel_t -
                0.5f * acceleration_ * decel_t * decel_t;
      vel_abs = peak_velocity_ - acceleration_ * decel_t;
      acc_abs = -acceleration_;
    }

    if (out.finished) {
      out.position = distance_;
      out.velocity = 0.0f;
      out.acceleration = 0.0f;
      return out;
    }

    out.position = direction_ * pos_abs;
    out.velocity = direction_ * vel_abs;
    out.acceleration = direction_ * acc_abs;
    return out;
  }

  Scalar duration() const { return duration_; }
  Scalar distance() const { return distance_; }
  Scalar peak_velocity() const { return peak_velocity_; }
  Scalar acceleration() const { return acceleration_; }
  Scalar accel_time() const { return accel_time_; }
  Scalar cruise_time() const { return cruise_time_; }
  bool valid() const { return valid_; }

 private:
  void reset() {
    distance_ = 0.0f;
    direction_ = 1.0f;
    abs_distance_ = 0.0f;
    peak_velocity_ = 0.0f;
    acceleration_ = 0.0f;
    accel_time_ = 0.0f;
    cruise_time_ = 0.0f;
    duration_ = 0.0f;
    epsilon_ = kDefaultEpsilon;
    valid_ = false;
  }

  Scalar distance_;
  Scalar direction_;
  Scalar abs_distance_;
  Scalar peak_velocity_;
  Scalar acceleration_;
  Scalar accel_time_;
  Scalar cruise_time_;
  Scalar duration_;
  Scalar epsilon_;
  bool valid_;
};

}  // namespace mr::comp::traj
