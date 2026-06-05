#pragma once

/*
 * 多轴同步梯形速度曲线。
 *
 * 控制律（基于梯形曲线，各轴独立计算）：
 *   for each axis i:
 *     compute trapezoid profile with (distance_i, v_max[i], a_max[i])
 *   T_sync = max(T_i)  // 取最大持续时间
 *   for each axis i:
 *     scale time: t_i = T_i / T_sync * elapsed  // 时间归一化
 *     sample position_i = trapezoid.sample(t_i)
 *
 * 特性：
 *   - 各轴独立规划梯形曲线
 *   - 取最大持续时间作为同步周期
 *   - 时间归一化确保所有轴同时开始、同时结束
 *   - 保证多轴运动的时间同步性
 *
 * 使用示例（3轴）：
 *   // 初始化：配置规划器
 *   mr::comp::traj::SynchronizedTrapezoidProfile<3> profile;
 *   float distances[3] = {1.0f, 2.0f, 1.5f};
 *   float max_v[3] = {1.0f, 1.0f, 1.0f};
 *   float max_a[3] = {2.0f, 2.0f, 2.0f};
 *   profile.configure(distances, max_v, max_a);
 *   float start_time = get_current_time();
 *
 *   // 控制循环中（每周期执行）：
 *   float elapsed = get_current_time() - start_time;
 *   for (int i = 0; i < 3; ++i) {
 *     auto sample = profile.sample_axis(i, elapsed);  // 获取各轴采样
 *   }
 */

#include "trapezoid.hpp"

namespace mr::comp::traj {

template <int N>
class SynchronizedTrapezoidProfile {
 public:
  SynchronizedTrapezoidProfile() : duration_(0.0f), valid_(false) {}

  bool configure(const Scalar* distances,
                 const Scalar* max_velocities,
                 const Scalar* max_accelerations,
                 Scalar epsilon = kDefaultEpsilon) {
    valid_ = false;
    duration_ = 0.0f;
    if (distances == nullptr || max_velocities == nullptr ||
        max_accelerations == nullptr) {
      return false;
    }

    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      const Scalar min_time = TrapezoidProfile::min_duration(
          distances[i], max_velocities[i], max_accelerations[i], epsilon);
      if (min_time < 0.0f) {
        return false;
      }
      if (min_time > duration_) {
        duration_ = min_time;
      }
    }

    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      if (!profiles_[i].configure_synchronized(
              distances[i], max_velocities[i], max_accelerations[i],
              duration_, epsilon)) {
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

  const TrapezoidProfile& axis(uint16_t index) const {
    return profiles_[index];
  }

  Scalar duration() const { return duration_; }
  bool valid() const { return valid_; }

 private:
  TrapezoidProfile profiles_[N];
  Scalar duration_;
  bool valid_;
};

}  // namespace mr::comp::traj
