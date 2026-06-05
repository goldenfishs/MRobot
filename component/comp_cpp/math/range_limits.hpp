/**
 ******************************************************************************
 * @file    range_limits.hpp
 * @brief   Range limit and projection utilities for multi-DOF systems.
 *          关节/轴范围限制与投影工具
 * @author  XuMing Yuan
 ******************************************************************************
 */

#pragma once

#include <stdint.h>

#include "scalar.hpp"

namespace mr::component::math {

enum class RangeLimitMode : uint8_t {
  kClamp = 0,
  kWrapThenClamp,
};

template <int N>
struct RangeLimits {
  Scalar lower[N];
  Scalar upper[N];
  bool enabled[N];

  RangeLimits() {
    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      lower[i] = 0.0f;
      upper[i] = 0.0f;
      enabled[i] = false;
    }
  }

  void enable_all() {
    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      enabled[i] = true;
    }
  }

  void disable_all() {
    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      enabled[i] = false;
    }
  }

  void set(uint16_t index, Scalar lower_bound, Scalar upper_bound) {
    if (index >= static_cast<uint16_t>(N)) {
      return;
    }
    lower[index] = lower_bound;
    upper[index] = upper_bound;
    enabled[index] = true;
  }
};

template <int N>
struct RangeProjection {
  Scalar lower[N];
  Scalar upper[N];
  bool enabled[N];

  RangeProjection() {
    for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
      lower[i] = 0.0f;
      upper[i] = 0.0f;
      enabled[i] = false;
    }
  }

  void set(uint16_t index, Scalar lower_bound, Scalar upper_bound) {
    if (index >= static_cast<uint16_t>(N)) {
      return;
    }
    lower[index] = lower_bound;
    upper[index] = upper_bound;
    enabled[index] = true;
  }
};

inline Scalar clamp_to_range(Scalar value, Scalar lower, Scalar upper) {
  return clamp_scalar(value, lower, upper);
}

inline Scalar wrap_to_range_then_clamp(Scalar value,
                                       Scalar projection_lower,
                                       Scalar projection_upper,
                                       Scalar limit_lower,
                                       Scalar limit_upper,
                                       Scalar epsilon = kDefaultEpsilon) {
  return clamp_to_range(wrap_to_range(value, projection_lower, projection_upper,
                                      epsilon),
                        limit_lower, limit_upper);
}

template <int N>
inline bool has_any_range_limit(const RangeLimits<N>& limits) {
  for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
    if (limits.enabled[i]) {
      return true;
    }
  }
  return false;
}

template <int N>
inline bool is_within_range_limits(const RangeLimits<N>& limits,
                                   const Scalar* values,
                                   Scalar margin = kDefaultEpsilon) {
  if (values == nullptr) {
    return false;
  }

  for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
    if (!limits.enabled[i]) {
      continue;
    }
    if (values[i] < limits.lower[i] - margin) {
      return false;
    }
    if (values[i] > limits.upper[i] + margin) {
      return false;
    }
  }
  return true;
}

template <int N>
inline void apply_range_limits(const RangeLimits<N>& limits,
                               const Scalar* values,
                               Scalar* out,
                               RangeLimitMode mode = RangeLimitMode::kClamp,
                               const RangeProjection<N>* projection = nullptr,
                               Scalar epsilon = kDefaultEpsilon) {
  if (values == nullptr || out == nullptr) {
    return;
  }

  for (uint16_t i = 0; i < static_cast<uint16_t>(N); ++i) {
    Scalar value = values[i];
    if (mode == RangeLimitMode::kWrapThenClamp && projection != nullptr &&
        projection->enabled[i]) {
      value = wrap_to_range(value, projection->lower[i], projection->upper[i],
                            epsilon);
    }
    if (limits.enabled[i]) {
      value = clamp_to_range(value, limits.lower[i], limits.upper[i]);
    }
    out[i] = value;
  }
}

}  // namespace mr::component::math
