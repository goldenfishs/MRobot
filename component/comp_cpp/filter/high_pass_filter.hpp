#pragma once

/*
 * 一阶高通滤波器。
 *
 * 用于去除慢速漂移或直流偏置，同时保留快速变化：
 *
 *   auto filter = mr::comp::filter::high_pass::Build(
 *       2.0f,     // 截止频率 Hz
 *       1000.0f   // 采样频率 Hz
 *   );
 *
 *   filter.Reset(initial_sample);
 *   float y = filter.Update(sample);
 *
 * 如果循环周期不固定，每次更新时传入本次实际间隔 dt_s，单位为秒：
 *
 *   float y = filter.Update(sample, dt_s);
 *
 * cutoff_freq_hz <= 0 时，滤波器旁路，直接返回输入值。
 */

#include "component/filter/filter_types.hpp"

namespace mr::comp::filter {

struct high_pass_config { 
  Scalar sample_freq_hz = kDefaultSampleFreqHz;
  Scalar cutoff_freq_hz = 0.0f;
};

class high_pass {
 public:
  using Config = high_pass_config;

  static high_pass Build(const Config& config) { return high_pass(config); }

  static high_pass Build(Scalar cutoff_freq_hz,
                         Scalar sample_freq_hz = kDefaultSampleFreqHz) {
    Config config{};
    config.cutoff_freq_hz = cutoff_freq_hz;
    config.sample_freq_hz = sample_freq_hz;
    return high_pass(config);
  }

  high_pass() { Configure(Config{}); }
  explicit high_pass(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    alpha_ = MakeAlpha(config_.cutoff_freq_hz, config_.sample_freq_hz);
    bypass_ = !detail::enabled_frequency(config_.cutoff_freq_hz);
    Reset();
  }

  void SetCutoff(Scalar cutoff_freq_hz) {
    config_.cutoff_freq_hz = cutoff_freq_hz;
    alpha_ = MakeAlpha(config_.cutoff_freq_hz, config_.sample_freq_hz);
    bypass_ = !detail::enabled_frequency(config_.cutoff_freq_hz);
  }

  void SetSampleFreq(Scalar sample_freq_hz) {
    config_.sample_freq_hz = sample_freq_hz;
    alpha_ = MakeAlpha(config_.cutoff_freq_hz, config_.sample_freq_hz);
  }

  void Reset(Scalar sample = 0.0f) {
    last_input_ = sample;
    output_ = 0.0f;
    initialized_ = true;
  }

  Scalar Update(Scalar sample) { return UpdateWithAlpha(sample, alpha_); }

  Scalar Update(Scalar sample, Scalar dt_s) {
    const Scalar sample_freq_hz =
        sample_freq_from_dt(dt_s, config_.sample_freq_hz);
    return UpdateWithAlpha(sample,
                           MakeAlpha(config_.cutoff_freq_hz, sample_freq_hz));
  }

  Scalar Apply(Scalar sample) { return Update(sample); }
  Scalar Apply(Scalar sample, Scalar dt_s) { return Update(sample, dt_s); }

  const Config& config() const { return config_; }
  Scalar output() const { return output_; }
  bool bypassed() const { return bypass_; }

 private:
  static Scalar MakeAlpha(Scalar cutoff_freq_hz, Scalar sample_freq_hz) {
    if (!detail::enabled_frequency(cutoff_freq_hz)) {
      return 0.0f;
    }
    const Scalar dt = dt_from_sample_freq(sample_freq_hz);
    const Scalar rc =
        1.0f / (mr::component::math::kTwoPi * cutoff_freq_hz);
    if (!is_usable_scalar(rc)) {
      return 0.0f;
    }
    return rc / (rc + dt);
  }

  Scalar UpdateWithAlpha(Scalar sample, Scalar alpha) {
    if (!is_usable_scalar(sample)) {
      return output_;
    }
    if (bypass_) {
      last_input_ = sample;
      output_ = sample;
      initialized_ = true;
      return output_;
    }
    if (!initialized_) {
      Reset(sample);
      return output_;
    }

    const Scalar output = alpha * (output_ + sample - last_input_);
    last_input_ = sample;
    if (is_usable_scalar(output)) {
      output_ = output;
    }
    return output_;
  }

  Config config_{};
  Scalar alpha_ = 0.0f;
  Scalar last_input_ = 0.0f;
  Scalar output_ = 0.0f;
  bool bypass_ = true;
  bool initialized_ = false;
};

}  // namespace mr::comp::filter
