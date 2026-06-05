#pragma once

/*
 * S曲线速度规划器。
 *
 * 控制律（七段式）：
 *   Phase 1 (0 <= t < tau1): 加加速
 *     jerk = j, acceleration = j*t, velocity = 0.5*j*t^2, position = j*t^3/6
 *
 *   Phase 2 (tau1 <= t < tau1+tau2): 匀加速
 *     jerk = 0, acceleration = a, velocity = v1 + a*(t-tau1)
 *     position = d1 + v1*(t-tau1) + 0.5*a*(t-tau1)^2
 *
 *   Phase 3 (tau1+tau2 <= t < tau1+tau2+tau3): 减加速
 *     jerk = -j, acceleration = a - j*(t-t1), velocity = ...
 *
 *   Phase 4 (tau1+tau2+tau3 <= t < tau1+tau2+tau3+tau4): 匀速
 *     jerk = 0, acceleration = 0, velocity = v_peak
 *
 *   Phase 5-7: 对称减速过程 (jerk = -j, 0, +j)
 *
 * 特性：
 *   - 加速度连续，冲击（jerk）有界
 *   - 运动更平滑，机械振动更小
 *   - 相比梯形曲线，加减速过程更柔和
 *
 * 使用示例：
 *   // 初始化：配置规划器
 *   auto planner = mr::comp::traj::SCurveProfile();
 *   planner.configure(distance, max_velocity, max_acceleration, max_jerk);
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

class SCurveProfile {
 public:
  SCurveProfile()
      : distance_(0.0f),
        direction_(1.0f),
        abs_distance_(0.0f),
        max_velocity_(0.0f),
        max_acceleration_(0.0f),
        max_jerk_(0.0f),
        duration_(0.0f),
        tau1_(0.0f),
        tau2_(0.0f),
        tau3_(0.0f),
        tau4_(0.0f),
        tau5_(0.0f),
        tau6_(0.0f),
        tau7_(0.0f),
        valid_(false) {}

  bool configure(Scalar distance,
                 Scalar max_velocity,
                 Scalar max_acceleration,
                 Scalar max_jerk,
                 Scalar epsilon = kDefaultEpsilon) {
    reset();
    if (!is_finite_scalar(distance) || !is_finite_scalar(max_velocity) ||
        !is_finite_scalar(max_acceleration) || !is_finite_scalar(max_jerk)) {
      return false;
    }

    abs_distance_ = abs_scalar(distance);
    direction_ = (distance >= 0.0f) ? 1.0f : -1.0f;

    if (abs_distance_ <= epsilon) {
      valid_ = true;
      return true;
    }

    max_velocity_ = abs_scalar(max_velocity);
    max_acceleration_ = abs_scalar(max_acceleration);
    max_jerk_ = abs_scalar(max_jerk);

    if (max_velocity_ <= epsilon || max_acceleration_ <= epsilon ||
        max_jerk_ <= epsilon) {
      return false;
    }

    if (!compute_time_intervals(epsilon)) {
      return false;
    }

    duration_ = tau1_ + tau2_ + tau3_ + tau4_ + tau5_ + tau6_ + tau7_;
    valid_ = true;
    return true;
  }

  ScalarMotionSample sample(Scalar elapsed) const {
    ScalarMotionSample out;
    if (!valid_) {
      return out;
    }

    out.valid = true;
    if (duration_ <= kDefaultEpsilon) {
      out.position = distance_;
      out.finished = true;
      return out;
    }

    const Scalar t = clamp_scalar(elapsed, 0.0f, duration_);
    out.finished = (elapsed >= duration_);

    Scalar pos_abs = 0.0f;
    Scalar vel_abs = 0.0f;
    Scalar acc_abs = 0.0f;
    Scalar jerk_abs = 0.0f;

    if (t <= tau1_) {
      const Scalar t2 = t * t;
      pos_abs = (max_jerk_ / 6.0f) * t2 * t;
      vel_abs = 0.5f * max_jerk_ * t2;
      acc_abs = max_jerk_ * t;
      jerk_abs = max_jerk_;
    } else if (t <= tau1_ + tau2_) {
      const Scalar t_rel = t - tau1_;
      const Scalar v1 = 0.5f * max_jerk_ * tau1_ * tau1_;
      pos_abs = (max_jerk_ / 6.0f) * tau1_ * tau1_ * tau1_ +
                v1 * t_rel + 0.5f * max_acceleration_ * t_rel * t_rel;
      vel_abs = v1 + max_acceleration_ * t_rel;
      acc_abs = max_acceleration_;
      jerk_abs = 0.0f;
    } else if (t <= tau1_ + tau2_ + tau3_) {
      const Scalar t_rel = t - tau1_ - tau2_;
      const Scalar t1_sq = tau1_ * tau1_;
      const Scalar t1_cu = t1_sq * tau1_;
      const Scalar v1 = 0.5f * max_jerk_ * t1_sq;
      const Scalar d1 = (max_jerk_ / 6.0f) * t1_cu;
      const Scalar d2 = v1 * tau2_ + 0.5f * max_acceleration_ * tau2_ * tau2_;
      pos_abs = d1 + d2 + v1 * t_rel + max_acceleration_ * tau2_ * t_rel +
                0.5f * max_acceleration_ * t_rel * t_rel -
                (max_jerk_ / 6.0f) * t_rel * t_rel * t_rel;
      vel_abs = v1 + max_acceleration_ * (tau2_ + t_rel) -
                0.5f * max_jerk_ * t_rel * t_rel;
      acc_abs = max_acceleration_ - max_jerk_ * t_rel;
      jerk_abs = -max_jerk_;
    } else if (t <= tau1_ + tau2_ + tau3_ + tau4_) {
      const Scalar t_rel = t - tau1_ - tau2_ - tau3_;
      const Scalar v_cruise = max_velocity_;
      pos_abs = compute_pos_at_tau3() + v_cruise * t_rel;
      vel_abs = v_cruise;
      acc_abs = 0.0f;
      jerk_abs = 0.0f;
    } else if (t <= tau1_ + tau2_ + tau3_ + tau4_ + tau5_) {
      const Scalar t_rel = t - tau1_ - tau2_ - tau3_ - tau4_;
      pos_abs = compute_pos_at_tau3() + max_velocity_ * tau4_ +
                0.5f * max_jerk_ * t_rel * t_rel * t_rel;
      vel_abs = max_velocity_ - 0.5f * max_jerk_ * t_rel * t_rel;
      acc_abs = -max_jerk_ * t_rel;
      jerk_abs = -max_jerk_;
    } else if (t <= tau1_ + tau2_ + tau3_ + tau4_ + tau5_ + tau6_) {
      const Scalar t_rel = t - tau1_ - tau2_ - tau3_ - tau4_ - tau5_;
      const Scalar v_at_5 = max_velocity_ - 0.5f * max_jerk_ * tau5_ * tau5_;
      const Scalar d_at_5 =
          compute_pos_at_tau3() + max_velocity_ * tau4_ +
          (max_jerk_ / 6.0f) * tau5_ * tau5_ * tau5_;
      pos_abs = d_at_5 + v_at_5 * t_rel - 0.5f * max_acceleration_ * t_rel * t_rel;
      vel_abs = v_at_5 - max_acceleration_ * t_rel;
      acc_abs = -max_acceleration_;
      jerk_abs = 0.0f;
    } else if (t < duration_) {
      const Scalar t_rel = t - tau1_ - tau2_ - tau3_ - tau4_ - tau5_ - tau6_;
      const Scalar v_at_6 =
          max_velocity_ - 0.5f * max_jerk_ * tau5_ * tau5_ - max_acceleration_ * tau6_;
      const Scalar d_at_6 =
          compute_pos_at_tau3() + max_velocity_ * tau4_ +
          (max_jerk_ / 6.0f) * tau5_ * tau5_ * tau5_ +
          v_at_6 * tau6_ - 0.5f * max_acceleration_ * tau6_ * tau6_;
      pos_abs = d_at_6 + v_at_6 * t_rel -
                0.5f * max_acceleration_ * tau6_ * t_rel +
                0.5f * max_acceleration_ * t_rel * t_rel +
                (max_jerk_ / 6.0f) * t_rel * t_rel * t_rel;
      vel_abs = v_at_6 - 0.5f * max_acceleration_ * tau6_ +
                max_acceleration_ * t_rel + 0.5f * max_jerk_ * t_rel * t_rel;
      acc_abs = -max_acceleration_ + max_jerk_ * t_rel;
      jerk_abs = max_jerk_;
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
  bool valid() const { return valid_; }

 private:
  Scalar compute_pos_at_tau3() const {
    const Scalar t1_sq = tau1_ * tau1_;
    const Scalar t1_cu = t1_sq * tau1_;
    const Scalar t2_sq = tau2_ * tau2_;
    const Scalar t3_sq = tau3_ * tau3_;
    const Scalar t5_sq = tau5_ * tau5_;
    const Scalar t5_cu = t5_sq * tau5_;

    const Scalar d1 = (max_jerk_ / 6.0f) * t1_cu;
    const Scalar v1 = 0.5f * max_jerk_ * t1_sq;
    const Scalar d2 = v1 * tau2_ + 0.5f * max_acceleration_ * t2_sq;
    const Scalar v2 = v1 + max_acceleration_ * tau2_;
    const Scalar d3 =
        v2 * tau3_ - (max_jerk_ / 6.0f) * tau3_ * t3_sq;
    const Scalar d5 = v2 * tau4_;
    const Scalar d6 = v2 * tau5_ + (max_jerk_ / 6.0f) * t5_cu;

    return d1 + d2 + d3 + d5 + d6;
  }

  void reset() {
    distance_ = 0.0f;
    direction_ = 1.0f;
    abs_distance_ = 0.0f;
    max_velocity_ = 0.0f;
    max_acceleration_ = 0.0f;
    max_jerk_ = 0.0f;
    duration_ = 0.0f;
    tau1_ = tau2_ = tau3_ = tau4_ = tau5_ = tau6_ = tau7_ = 0.0f;
    valid_ = false;
  }

  bool compute_time_intervals(Scalar epsilon) {
    const Scalar j = max_jerk_;
    const Scalar a = max_acceleration_;
    const Scalar v = max_velocity_;

    const Scalar t_ja = j * a;
    if (t_ja <= epsilon) {
      return false;
    }

    const Scalar tau1 = a / j;
    const Scalar tau2 = tau1;
    const Scalar tau3 = tau1;

    Scalar v_limit_by_acc = 0.5f * j * tau1 * tau1 * 3.0f;
    Scalar d_limit_by_acc = v_limit_by_acc * tau1 * 2.0f;

    if (d_limit_by_acc >= abs_distance_) {
      Scalar discriminant = 9.0f * abs_distance_ / j - 2.0f * a * a * a / (j * j);
      if (discriminant < 0.0f) {
        return false;
      }
      const Scalar sqrt_disc = sqrtf(discriminant);
      tau1 = powf(0.5f * abs_distance_ / j + sqrt_disc * 0.5f, 1.0f / 3.0f) -
             powf(0.5f * abs_distance_ / j - sqrt_disc * 0.5f, 1.0f / 3.0f);
      tau1 = clamp_scalar(tau1, epsilon, abs_distance_ / v);
      tau2 = tau1;
      tau3 = tau1;
      tau4 = 0.0f;
      tau5 = tau1;
      tau6 = tau1;
      tau7 = tau1;
    } else {
      const Scalar v_ramp = 0.5f * j * tau1 * tau1 * 3.0f;
      const Scalar v_cruise = v_ramp;
      tau4 = (abs_distance_ - d_limit_by_acc - v_cruise * tau1 * 2.0f) / v_cruise;

      if (tau4 < 0.0f) {
        return false;
      }

      tau5 = tau1;
      tau6 = tau1;
      tau7 = tau1;
    }

    tau1_ = tau1;
    tau2_ = tau2;
    tau3_ = tau3;
    tau4_ = tau4;
    tau5_ = tau5;
    tau6_ = tau6;
    tau7_ = tau7;

    return true;
  }

  Scalar distance_;
  Scalar direction_;
  Scalar abs_distance_;
  Scalar max_velocity_;
  Scalar max_acceleration_;
  Scalar max_jerk_;
  Scalar duration_;
  Scalar tau1_;
  Scalar tau2_;
  Scalar tau3_;
  Scalar tau4_;
  Scalar tau5_;
  Scalar tau6_;
  Scalar tau7_;
  bool valid_;
};

template <int N>
class SynchronizedSCurveProfile {
 public:
  SynchronizedSCurveProfile() : duration_(0.0f), valid_(false) {}

  bool configure(const Scalar* distances,
                 const Scalar* max_velocities,
                 const Scalar* max_accelerations,
                 const Scalar* max_jerks,
                 Scalar epsilon = kDefaultEpsilon) {
    valid_ = false;
    duration_ = 0.0f;

    if (distances == nullptr || max_velocities == nullptr ||
        max_accelerations == nullptr || max_jerks == nullptr) {
      return false;
    }

    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      Scalar duration_i;
      if (!compute_duration(distances[i], max_velocities[i],
                           max_accelerations[i], max_jerks[i],
                           &duration_i, epsilon)) {
        return false;
      }
      if (duration_i > duration_) {
        duration_ = duration_i;
      }
    }

    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      if (!profiles_[i].configure(distances[i], max_velocities[i],
                                  max_accelerations[i], max_jerks[i], epsilon)) {
        valid_ = false;
        duration_ = 0.0f;
        return false;
      }
    }

    valid_ = true;
    return true;
  }

  ScalarMotionSample sample_axis(uint16_t index, Scalar elapsed) const {
    if (index >= static_cast<uint16_t>(N)) {
      return ScalarMotionSample();
    }
    return profiles_[index].sample(elapsed);
  }

  Scalar duration() const { return duration_; }
  bool valid() const { return valid_; }

 private:
  bool compute_duration(Scalar distance,
                       Scalar max_velocity,
                       Scalar max_acceleration,
                       Scalar max_jerk,
                       Scalar* duration_out,
                       Scalar epsilon) const {
    if (duration_out == nullptr) {
      return false;
    }
    *duration_out = 0.0f;

    const Scalar d = abs_scalar(distance);
    if (d <= epsilon) {
      return true;
    }

    const Scalar v = abs_scalar(max_velocity);
    const Scalar a = abs_scalar(max_acceleration);
    const Scalar j = abs_scalar(max_jerk);

    if (v <= epsilon || a <= epsilon || j <= epsilon) {
      return false;
    }

    const Scalar tau_a = a / j;
    const Scalar v_ramp = 0.5f * j * tau_a * tau_a * 3.0f;

    Scalar tau4;
    if (v_ramp >= v) {
      const Scalar discriminant =
          9.0f * d / j - 2.0f * a * a * a / (j * j * j);
      if (discriminant < 0.0f) {
        return false;
      }
      const Scalar sqrt_disc = sqrtf(discriminant);
      const Scalar tau1 =
          powf(0.5f * d / j + sqrt_disc * 0.5f, 1.0f / 3.0f) -
          powf(0.5f * d / j - sqrt_disc * 0.5f, 1.0f / 3.0f);
      tau4 = 0.0f;
      *duration_out = tau1 * 6.0f;
    } else {
      const Scalar tau1 = tau_a;
      const Scalar d_ramp = v_ramp * tau1 * 2.0f;
      const Scalar v_cruise = v_ramp;
      tau4 = (d - d_ramp) / v_cruise;

      if (tau4 < 0.0f) {
        return false;
      }

      *duration_out = tau1 * 4.0f + tau4 + tau1 * 2.0f;
    }

    return true;
  }

  SCurveProfile profiles_[N];
  Scalar duration_;
  bool valid_;
};

}  // namespace mr::comp::traj
