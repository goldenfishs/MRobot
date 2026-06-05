#pragma once

/*
 * 二阶陷波滤波器。
 *
 * 用于抑制窄频段振动或共振频率：
 *
 *   auto filter = mr::comp::filter::notch::Build(
 *       50.0f,    // 陷波中心频率 Hz
 *       5.0f,     // 带宽 Hz
 *       1000.0f   // 采样频率 Hz
 *   );
 *
 *   filter.Reset(initial_value);
 *   float y = filter.Update(sample);
 *
 * 如果循环周期不固定，每次更新时传入本次实际间隔 dt_s，单位为秒：
 *
 *   float y = filter.Update(sample, dt_s);
 *
 * notch_freq_hz <= 0、bandwidth_hz <= 0 或 notch_freq_hz >= 奈奎斯特频率时，
 * 滤波器旁路，直接返回输入值。
 */

#include <cmath>

#include "component/filter/filter_types.hpp"

namespace mr::comp::filter {

struct notch_config {
  Scalar sample_freq_hz = kDefaultSampleFreqHz;
  Scalar notch_freq_hz = 0.0f;
  Scalar bandwidth_hz = 0.0f;
};

class notch {
 public:
  using Config = notch_config;

  static notch Build(const Config& config) { return notch(config); }

  static notch Build(Scalar notch_freq_hz,
                     Scalar bandwidth_hz,
                     Scalar sample_freq_hz = kDefaultSampleFreqHz) {
    Config config{};
    config.notch_freq_hz = notch_freq_hz;
    config.bandwidth_hz = bandwidth_hz;
    config.sample_freq_hz = sample_freq_hz;
    return notch(config);
  }

  notch() { Configure(Config{}); }
  explicit notch(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    coeff_ = MakeCoefficients(config_.notch_freq_hz, config_.bandwidth_hz,
                              config_.sample_freq_hz);
    state_ = {};
  }

  void SetNotch(Scalar notch_freq_hz, Scalar bandwidth_hz) {
    config_.notch_freq_hz = notch_freq_hz;
    config_.bandwidth_hz = bandwidth_hz;
    coeff_ = MakeCoefficients(config_.notch_freq_hz, config_.bandwidth_hz,
                              config_.sample_freq_hz);
  }

  void SetSampleFreq(Scalar sample_freq_hz) {
    config_.sample_freq_hz = sample_freq_hz;
    coeff_ = MakeCoefficients(config_.notch_freq_hz, config_.bandwidth_hz,
                              config_.sample_freq_hz);
  }

  void Reset(Scalar output = 0.0f) { state_.Reset(coeff_, output); }

  Scalar Update(Scalar sample) { return state_.Update(coeff_, sample); }

  Scalar Update(Scalar sample, Scalar dt_s) {
    const Scalar sample_freq_hz =
        sample_freq_from_dt(dt_s, config_.sample_freq_hz);
    const detail::biquad_coefficients coeff = MakeCoefficients(
        config_.notch_freq_hz, config_.bandwidth_hz, sample_freq_hz);
    return state_.Update(coeff, sample);
  }

  Scalar Apply(Scalar sample) { return Update(sample); }
  Scalar Apply(Scalar sample, Scalar dt_s) { return Update(sample, dt_s); }

  const Config& config() const { return config_; }
  Scalar output() const { return state_.output(); }
  bool bypassed() const { return coeff_.bypass; }

 private:
  static detail::biquad_coefficients MakeCoefficients(Scalar notch_freq_hz,
                                                       Scalar bandwidth_hz,
                                                       Scalar sample_freq_hz) {
    detail::biquad_coefficients coeff{};
    sample_freq_hz = detail::sanitize_sample_freq(sample_freq_hz);
    if (!detail::enabled_frequency(notch_freq_hz) ||
        !detail::enabled_frequency(bandwidth_hz)) {
      return coeff;
    }

    const Scalar nyquist = detail::nyquist_frequency(sample_freq_hz);
    if (notch_freq_hz >= nyquist) {
      return coeff;
    }

    const Scalar alpha =
        tanf(mr::component::math::kPi * bandwidth_hz / sample_freq_hz);
    const Scalar beta =
        -cosf(mr::component::math::kTwoPi * notch_freq_hz / sample_freq_hz);
    if (!is_usable_scalar(alpha) || !is_usable_scalar(beta)) {
      return coeff;
    }

    const Scalar a0_inv = 1.0f / (alpha + 1.0f);
    if (!is_usable_scalar(a0_inv)) {
      return coeff;
    }

    coeff.b0 = a0_inv;
    coeff.b1 = 2.0f * beta * a0_inv;
    coeff.b2 = a0_inv;
    coeff.a1 = coeff.b1;
    coeff.a2 = (1.0f - alpha) * a0_inv;
    coeff.bypass = false;
    return coeff;
  }

  Config config_{};
  detail::biquad_coefficients coeff_{};
  detail::biquad_state state_{};
};

}  // namespace mr::comp::filter
