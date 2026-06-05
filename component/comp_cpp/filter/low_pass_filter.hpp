#pragma once

/*
 * 二阶低通滤波器。
 *
 * 用于滤除高频噪声，同时保留低频运动趋势：
 *
 *   auto filter = mr::comp::filter::low_pass::Build(
 *       30.0f,    // 截止频率 Hz
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
 * cutoff_freq_hz <= 0 或 cutoff_freq_hz >= 奈奎斯特频率时，滤波器旁路，
 * 直接返回输入值。
 */

#include <cmath>

#include "component/filter/filter_types.hpp"

namespace mr::comp::filter {

struct low_pass_config {
  Scalar sample_freq_hz = kDefaultSampleFreqHz;
  Scalar cutoff_freq_hz = 0.0f;
};

class low_pass {
 public:
  using Config = low_pass_config;

  static low_pass Build(const Config& config) { return low_pass(config); }

  static low_pass Build(Scalar cutoff_freq_hz,
                        Scalar sample_freq_hz = kDefaultSampleFreqHz) {
    Config config{};
    config.cutoff_freq_hz = cutoff_freq_hz;
    config.sample_freq_hz = sample_freq_hz;
    return low_pass(config);
  }

  low_pass() { Configure(Config{}); }
  explicit low_pass(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    coeff_ = MakeCoefficients(config_.cutoff_freq_hz, config_.sample_freq_hz);
    state_ = {};
  }

  void SetCutoff(Scalar cutoff_freq_hz) {
    config_.cutoff_freq_hz = cutoff_freq_hz;
    coeff_ = MakeCoefficients(config_.cutoff_freq_hz, config_.sample_freq_hz);
  }

  void SetSampleFreq(Scalar sample_freq_hz) {
    config_.sample_freq_hz = sample_freq_hz;
    coeff_ = MakeCoefficients(config_.cutoff_freq_hz, config_.sample_freq_hz);
  }

  void Reset(Scalar output = 0.0f) { state_.Reset(coeff_, output); }

  Scalar Update(Scalar sample) { return state_.Update(coeff_, sample); }

  Scalar Update(Scalar sample, Scalar dt_s) {
    const Scalar sample_freq_hz =
        sample_freq_from_dt(dt_s, config_.sample_freq_hz);
    const detail::biquad_coefficients coeff =
        MakeCoefficients(config_.cutoff_freq_hz, sample_freq_hz);
    return state_.Update(coeff, sample);
  }

  Scalar Apply(Scalar sample) { return Update(sample); }
  Scalar Apply(Scalar sample, Scalar dt_s) { return Update(sample, dt_s); }

  const Config& config() const { return config_; }
  Scalar output() const { return state_.output(); }
  bool bypassed() const { return coeff_.bypass; }

 private:
  static detail::biquad_coefficients MakeCoefficients(Scalar cutoff_freq_hz,
                                                       Scalar sample_freq_hz) {
    detail::biquad_coefficients coeff{};
    sample_freq_hz = detail::sanitize_sample_freq(sample_freq_hz);
    if (!detail::enabled_frequency(cutoff_freq_hz)) {
      return coeff;
    }

    const Scalar nyquist = detail::nyquist_frequency(sample_freq_hz);
    if (cutoff_freq_hz >= nyquist) {
      return coeff;
    }

    const Scalar omega =
        tanf(mr::component::math::kPi * cutoff_freq_hz / sample_freq_hz);
    if (!is_usable_scalar(omega)) {
      return coeff;
    }

    const Scalar omega_sq = mr::component::math::square_scalar(omega);
    constexpr Scalar kSqrt2 = 1.41421356237309504880f;
    const Scalar normalizer = 1.0f / (1.0f + kSqrt2 * omega + omega_sq);
    if (!is_usable_scalar(normalizer)) {
      return coeff;
    }

    coeff.b0 = omega_sq * normalizer;
    coeff.b1 = 2.0f * coeff.b0;
    coeff.b2 = coeff.b0;
    coeff.a1 = 2.0f * (omega_sq - 1.0f) * normalizer;
    coeff.a2 = (1.0f - kSqrt2 * omega + omega_sq) * normalizer;
    coeff.bypass = false;
    return coeff;
  }

  Config config_{};
  detail::biquad_coefficients coeff_{};
  detail::biquad_state state_{};
};

}  // namespace mr::comp::filter
