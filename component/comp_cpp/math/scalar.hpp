/**
 ******************************************************************************
 * @file    scalar.hpp
 * @brief   Scalar math utilities for embedded control systems.
 *          标量数学工具函数库
 * @author  XuMing Yuan
 ******************************************************************************
 */

#pragma once

#include <cmath>
#include <stddef.h>
#include <stdint.h>

namespace mr::component::math {

using Scalar = float;

constexpr Scalar kDefaultEpsilon = 1.0e-6f;
constexpr Scalar kFiniteLimit = 1.0e30f;
constexpr Scalar kPi = 3.14159265358979323846f;
constexpr Scalar kHalfPi = 0.5f * kPi;
constexpr Scalar kTwoPi = 2.0f * kPi;

inline Scalar abs_scalar(Scalar value) {
  return fabsf(value);
}

inline bool is_finite_scalar(Scalar value) {
  return (value == value) && (abs_scalar(value) <= kFiniteLimit);
}

inline bool is_positive_scalar(Scalar value,
                               Scalar epsilon = kDefaultEpsilon) {
  return is_finite_scalar(value) && value > epsilon;
}

inline Scalar clamp_scalar(Scalar value, Scalar lower, Scalar upper) {
  if (value < lower) {
    return lower;
  }
  if (value > upper) {
    return upper;
  }
  return value;
}

inline Scalar abs_clip_scalar(Scalar value, Scalar limit) {
  const Scalar positive_limit = abs_scalar(limit);
  return clamp_scalar(value, -positive_limit, positive_limit);
}

inline Scalar positive_or_zero(Scalar value) {
  return (is_finite_scalar(value) && value > 0.0f) ? value : 0.0f;
}

inline Scalar positive_or(Scalar value, Scalar fallback) {
  return (is_finite_scalar(value) && value > 0.0f) ? value : fallback;
}

inline Scalar square_scalar(Scalar value) {
  return value * value;
}

inline Scalar sanitize_positive(Scalar value,
                                Scalar fallback,
                                Scalar lower = kDefaultEpsilon,
                                Scalar upper = kFiniteLimit) {
  if (!is_finite_scalar(lower) || lower <= 0.0f) {
    lower = kDefaultEpsilon;
  }
  if (lower > kFiniteLimit) {
    lower = kFiniteLimit;
  }
  if (!is_finite_scalar(upper) || upper < lower) {
    upper = kFiniteLimit;
  }
  if (upper < lower) {
    upper = lower;
  }
  if (!is_finite_scalar(value) || value < lower) {
    value = fallback;
  }
  if (!is_finite_scalar(value) || value < lower) {
    value = lower;
  }
  return clamp_scalar(value, lower, upper);
}

inline Scalar sanitize_dt(Scalar dt,
                          Scalar fallback,
                          Scalar min_dt,
                          Scalar max_dt) {
  if (!is_finite_scalar(min_dt) || min_dt <= 0.0f) {
    min_dt = kDefaultEpsilon;
  }
  if (!is_finite_scalar(max_dt) || max_dt < min_dt) {
    max_dt = kFiniteLimit;
  }
  if (!is_finite_scalar(fallback) || fallback < min_dt) {
    fallback = min_dt;
  }
  if (!is_finite_scalar(dt) || dt <= 0.0f) {
    dt = fallback;
  }
  return clamp_scalar(dt, min_dt, max_dt);
}

inline Scalar wrap_to_range(Scalar value,
                            Scalar lower,
                            Scalar upper,
                            Scalar epsilon = kDefaultEpsilon) {
  const Scalar width = upper - lower;
  if (!is_finite_scalar(value) || !is_finite_scalar(lower) ||
      !is_finite_scalar(upper) || width <= epsilon) {
    return value;
  }

  Scalar wrapped = fmodf(value - lower, width);
  if (wrapped < 0.0f) {
    wrapped += width;
  }
  return lower + wrapped;
}

inline Scalar wrap_to_pi(Scalar angle) {
  Scalar wrapped =
      wrap_to_range(angle, -kPi, kPi, kDefaultEpsilon);
  if (wrapped >= kPi) {
    wrapped -= kTwoPi;
  }
  return wrapped;
}

inline Scalar wrap_error(Scalar error, Scalar range) {
  if (!is_finite_scalar(error) || !is_finite_scalar(range) ||
      range <= kDefaultEpsilon) {
    return error;
  }

  const Scalar half_range = 0.5f * range;
  while (error > half_range) {
    error -= range;
  }
  while (error < -half_range) {
    error += range;
  }
  return error;
}

inline Scalar angle_error(Scalar target, Scalar current) {
  return wrap_to_pi(target - current);
}

inline Scalar move_towards(Scalar current, Scalar target, Scalar max_step) {
  if (max_step <= 0.0f) {
    return target;
  }

  const Scalar delta = target - current;
  if (delta > max_step) {
    return current + max_step;
  }
  if (delta < -max_step) {
    return current - max_step;
  }
  return target;
}

inline Scalar apply_delta_limit(Scalar value,
                                Scalar previous,
                                Scalar max_delta) {
  return previous + abs_clip_scalar(value - previous, max_delta);
}

inline Scalar max_abs_array(const Scalar* values, uint32_t count) {
  if (values == nullptr) {
    return 0.0f;
  }

  Scalar max_abs = 0.0f;
  for (uint32_t i = 0U; i < count; ++i) {
    const Scalar abs_value = abs_scalar(values[i]);
    if (abs_value > max_abs) {
      max_abs = abs_value;
    }
  }
  return max_abs;
}

inline bool values_are_finite(const Scalar* values, uint32_t count) {
  if (values == nullptr) {
    return false;
  }

  for (uint32_t i = 0U; i < count; ++i) {
    if (!is_finite_scalar(values[i])) {
      return false;
    }
  }
  return true;
}

inline bool scale_to_abs_limit(Scalar* values,
                               uint32_t count,
                               Scalar limit) {
  if (values == nullptr || !is_finite_scalar(limit) || limit <= 0.0f) {
    return false;
  }

  const Scalar max_abs = max_abs_array(values, count);
  if (max_abs <= limit || max_abs <= 0.0f) {
    return false;
  }

  const Scalar scale = limit / max_abs;
  for (uint32_t i = 0U; i < count; ++i) {
    values[i] *= scale;
  }
  return true;
}

}  // namespace mr::component::math
