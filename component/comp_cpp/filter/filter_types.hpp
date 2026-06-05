#pragma once

/*
 * 滤波器组件共用类型和工具函数。
 *
 * 业务代码通常包含具体滤波器头文件或聚合头文件即可：
 *
 *   #include "component/filter/filter.hpp"
 *
 * 本文件保存通用标量别名、采样周期清洗工具，以及 low_pass 和 notch 共用的
 * 内部 biquad 状态。
 */

#include <stdint.h>

#include "component/math/scalar.hpp"

namespace mr::comp::filter {

using Scalar = mr::component::math::Scalar;

constexpr Scalar kDefaultSampleFreqHz = 1000.0f;
constexpr Scalar kDefaultDtS = 1.0f / kDefaultSampleFreqHz;
constexpr Scalar kMinDtS = 1.0e-6f;
constexpr Scalar kMaxDtS = 1.0f;

inline bool is_usable_scalar(Scalar value) {
  return mr::component::math::is_finite_scalar(value);
}

inline Scalar sanitize_dt(Scalar dt_s, Scalar fallback_dt_s = kDefaultDtS) {
  const Scalar fallback = mr::component::math::sanitize_positive(
      fallback_dt_s, kDefaultDtS, kMinDtS, kMaxDtS);
  if (!is_usable_scalar(dt_s) || dt_s <= 0.0f) {
    dt_s = fallback;
  }
  return mr::component::math::clamp_scalar(dt_s, kMinDtS, kMaxDtS);
}

inline Scalar dt_from_sample_freq(Scalar sample_freq_hz,
                                  Scalar fallback_hz = kDefaultSampleFreqHz) {
  const Scalar freq = mr::component::math::sanitize_positive(
      sample_freq_hz, fallback_hz, mr::component::math::kDefaultEpsilon,
      mr::component::math::kFiniteLimit);
  return 1.0f / freq;
}

inline Scalar sample_freq_from_dt(Scalar dt_s,
                                  Scalar fallback_hz = kDefaultSampleFreqHz) {
  const Scalar fallback_dt = dt_from_sample_freq(fallback_hz);
  return 1.0f / sanitize_dt(dt_s, fallback_dt);
}

struct sample_config {
  Scalar sample_freq_hz = kDefaultSampleFreqHz;

  Scalar dt_s() const { return dt_from_sample_freq(sample_freq_hz); }
};

namespace detail {

inline bool enabled_frequency(Scalar frequency_hz) {
  return mr::component::math::is_positive_scalar(
      frequency_hz, mr::component::math::kDefaultEpsilon);
}

inline Scalar sanitize_sample_freq(Scalar sample_freq_hz) {
  return mr::component::math::sanitize_positive(
      sample_freq_hz, kDefaultSampleFreqHz,
      mr::component::math::kDefaultEpsilon,
      mr::component::math::kFiniteLimit);
}

inline Scalar nyquist_frequency(Scalar sample_freq_hz) {
  return 0.5f * sanitize_sample_freq(sample_freq_hz);
}

struct biquad_coefficients {
  Scalar b0 = 1.0f;
  Scalar b1 = 0.0f;
  Scalar b2 = 0.0f;
  Scalar a1 = 0.0f;
  Scalar a2 = 0.0f;
  bool bypass = true;
};

class biquad_state {
 public:
  void Reset(Scalar output = 0.0f) {
    delay_1_ = output;
    delay_2_ = output;
    output_ = output;
    initialized_ = true;
  }

  void Reset(const biquad_coefficients& coeff, Scalar output) {
    Scalar delay = output;
    const Scalar gain = coeff.b0 + coeff.b1 + coeff.b2;
    if (mr::component::math::abs_scalar(gain) >
        mr::component::math::kDefaultEpsilon) {
      delay = output / gain;
    }
    if (!is_usable_scalar(delay)) {
      delay = output;
    }

    delay_1_ = delay;
    delay_2_ = delay;
    output_ = output;
    initialized_ = true;
  }

  Scalar Update(const biquad_coefficients& coeff, Scalar sample) {
    if (!is_usable_scalar(sample)) {
      return output_;
    }
    if (coeff.bypass) {
      Reset(sample);
      return output_;
    }
    if (!initialized_) {
      Reset(coeff, sample);
      return output_;
    }

    Scalar delay_0 = sample - delay_1_ * coeff.a1 - delay_2_ * coeff.a2;
    if (!is_usable_scalar(delay_0)) {
      delay_0 = sample;
    }

    const Scalar output =
        delay_0 * coeff.b0 + delay_1_ * coeff.b1 + delay_2_ * coeff.b2;
    if (!is_usable_scalar(output)) {
      return output_;
    }

    delay_2_ = delay_1_;
    delay_1_ = delay_0;
    output_ = output;
    return output_;
  }

  Scalar output() const { return output_; }
  bool initialized() const { return initialized_; }

 private:
  Scalar delay_1_ = 0.0f;
  Scalar delay_2_ = 0.0f;
  Scalar output_ = 0.0f;
  bool initialized_ = false;
};

}  // namespace detail

}  // namespace mr::comp::filter
