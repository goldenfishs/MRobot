#pragma once

/*
 * 轨迹规划基础类型定义。
 *
 * 定义轨迹规划所需的基础类型：
 *   - Scalar: 标量类型（float）
 *   - ScalarMotionSample: 单轴运动采样结果（位置、速度、加速度）
 *   - abs_scalar, clamp_scalar: 基础数学函数
 *
 * 业务代码通常包含具体轨迹头文件或聚合头文件即可：
 *
 *   #include "component/trajectory/trajectory.hpp"
 */

#include <stdint.h>

#include "component/math/scalar.hpp"

namespace mr::comp::traj {

using Scalar = mr::component::math::Scalar;

constexpr Scalar kDefaultEpsilon = mr::component::math::kDefaultEpsilon;
constexpr Scalar kDefaultFiniteLimit = mr::component::math::kFiniteLimit;

inline Scalar abs_scalar(Scalar value) {
  return mr::component::math::abs_scalar(value);
}

inline bool is_finite_scalar(Scalar value) {
  return mr::component::math::is_finite_scalar(value);
}

inline Scalar clamp_scalar(Scalar value, Scalar lower, Scalar upper) {
  return mr::component::math::clamp_scalar(value, lower, upper);
}

struct ScalarMotionSample {
  Scalar position;
  Scalar velocity;
  Scalar acceleration;
  bool valid;
  bool finished;

  ScalarMotionSample()
      : position(0.0f),
        velocity(0.0f),
        acceleration(0.0f),
        valid(false),
        finished(false) {}
};

}  // namespace mr::comp::traj
