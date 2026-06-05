#pragma once

/*
 * 控制律组件共用类型和工具函数。
 *
 * 定义控制器通用类型：
 *   - Scalar: 标量类型别名
 *   - SymmetricLimit: 对称限幅结构
 *   - RangeWrap: 周期角度误差处理
 *   - Step: 控制器采样结果
 *   - SlewRateLimiter: 输出斜率限制器
 *   - DerivativeMode: 微分项计算模式
 *
 * 业务代码通常包含具体控制器头文件或聚合头文件即可：
 *
 *   #include "component/controller/controller.hpp"
 */

#include <stdint.h>

#include "component/math/scalar.hpp"

namespace mr::comp::cntlr {

using Scalar = mr::component::math::Scalar;

constexpr Scalar kEpsilon = mr::component::math::kDefaultEpsilon;
constexpr Scalar kUnlimited = 0.0f;
constexpr Scalar kDefaultDt = 0.001f;
constexpr Scalar kDefaultSampleFreqHz = 1.0f / kDefaultDt;
constexpr Scalar kMinDt = 1.0e-6f;
constexpr Scalar kMaxDt = 1.0f;

enum class DerivativeMode : uint8_t {
  kNone = 0,
  kOnMeasurement,
  kExternal,
};

struct SymmetricLimit {
  Scalar value = kUnlimited;

  static constexpr SymmetricLimit Unlimited() { return {kUnlimited}; }
  static constexpr SymmetricLimit Abs(Scalar limit) { return {limit}; }

  bool enabled() const {
    return mr::component::math::is_finite_scalar(value) && value > 0.0f;
  }

  Scalar Apply(Scalar input) const {
    if (!enabled()) {
      return input;
    }
    return mr::component::math::clamp_scalar(input, -value, value);
  }
};

struct RangeWrap {
  Scalar range = kUnlimited;

  static constexpr RangeWrap Disabled() { return {kUnlimited}; }
  static constexpr RangeWrap Periodic(Scalar period) { return {period}; }

  bool enabled() const {
    return mr::component::math::is_finite_scalar(range) && range > 0.0f;
  }

  Scalar Error(Scalar setpoint, Scalar feedback) const {
    const Scalar raw_error = setpoint - feedback;
    if (!enabled()) {
      return raw_error;
    }

    const Scalar half = 0.5f * range;
    Scalar error = mr::component::math::wrap_to_range(raw_error, -half, half);
    if (error >= half) {
      error -= range;
    }
    return error;
  }
};

struct Step {
  Scalar output = 0.0f;
  Scalar setpoint = 0.0f;
  Scalar feedback = 0.0f;
  Scalar error = 0.0f;
  Scalar feedforward = 0.0f;
  Scalar p = 0.0f;
  Scalar i = 0.0f;
  Scalar d = 0.0f;
  bool valid = false;
  bool saturated = false;
};

inline Scalar SanitizeDt(Scalar dt_s, Scalar fallback = kDefaultDt) {
  if (!mr::component::math::is_finite_scalar(dt_s) || dt_s <= 0.0f) {
    dt_s = fallback;
  }
  if (dt_s < kMinDt) {
    return kMinDt;
  }
  if (dt_s > kMaxDt) {
    return kMaxDt;
  }
  return dt_s;
}

inline bool IsUsableScalar(Scalar value) {
  return mr::component::math::is_finite_scalar(value);
}

class SlewRateLimiter {
 public:
  static constexpr SlewRateLimiter Build(Scalar rate_limit_per_s,
                                         Scalar initial_value = 0.0f) {
    return SlewRateLimiter(rate_limit_per_s, initial_value);
  }

  constexpr SlewRateLimiter() = default;
  constexpr SlewRateLimiter(Scalar rate_limit_per_s, Scalar initial_value = 0.0f)
      : rate_limit_(SymmetricLimit::Abs(rate_limit_per_s)),
        last_(initial_value),
        initialized_(true) {}

  void Reset(Scalar value = 0.0f) {
    last_ = value;
    initialized_ = true;
  }

  Scalar Update(Scalar target, Scalar dt_s) {
    if (!initialized_) {
      Reset(target);
      return last_;
    }
    if (!IsUsableScalar(target)) {
      return last_;
    }
    if (!rate_limit_.enabled()) {
      last_ = target;
      return last_;
    }

    const Scalar max_delta = rate_limit_.value * SanitizeDt(dt_s);
    last_ += SymmetricLimit::Abs(max_delta).Apply(target - last_);
    return last_;
  }

  Scalar value() const { return last_; }
  SymmetricLimit rate_limit() const { return rate_limit_; }

 private:
  SymmetricLimit rate_limit_{};
  Scalar last_ = 0.0f;
  bool initialized_ = false;
};

}  // namespace mr::comp::cntlr
