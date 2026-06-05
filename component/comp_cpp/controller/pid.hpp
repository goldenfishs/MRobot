/*
 * 通用 PID 控制器（k,p,i,d 控制律）
 *
 * 控制律:
 *   error = setpoint - feedback
 *   k_error = k * error
 *   p_term = k_error * p
 *   integral_state += k_error * dt_s
 *   i_term = clamp(integral_state * i, +/-integral_output_limit)
 *   d_term = -d * d(k * feedback) / dt_s
 *   output = clamp(p_term + i_term + d_term, +/-output_limit)
 *
 *
 * api:
 *   #include "component/controller/pid.hpp"
 *
 *   namespace cntlr = mr::comp::cntlr;
 *
 *   auto pid = cntlr::pid::Build(
 *       1.0f,    // k
 *       2.0f,    // p
 *       0.1f,    // i
 *       0.01f,   // d
 *       6.0f,    // output_limit，0 表示不限幅
 *       1.0f,    // integral_output_limit，0 表示不限幅
 *       30.0f,   // derivative_cutoff_hz，0 表示不滤波
 *       500.0f   // control_freq_hz
 *   );
 *
 *   float out = pid.Update(target, feedback);
 *   float out = pid.Update(target, feedback, dt_s);
 *   float out = pid.Update(target, feedback, feedback_dot, dt_s);  // 手动输入微分项
 *
 *   pid.Reset();          // 清空积分、D 滤波状态、上次输出
 *   pid.ResetIntegral();  // 只清积分项
 *
 *   auto step = pid.Step(target, feedback, dt_s);  // 截取中间参数
 *
 */

#pragma once

#include "component/controller/controller_types.hpp"
#include "component/filter/low_pass_filter.hpp"

namespace mr::comp::cntlr {

struct pid_gains {
  Scalar k = 1.0f;
  Scalar p = 0.0f;
  Scalar i = 0.0f;
  Scalar d = 0.0f;
};

struct pid_config {
  pid_gains gains{};
  SymmetricLimit output_limit{};
  SymmetricLimit integral_output_limit{};
  SymmetricLimit output_rate_limit{};
  RangeWrap error_wrap{};
  DerivativeMode derivative_mode = DerivativeMode::kOnMeasurement;
  Scalar derivative_cutoff_hz = 0.0f;
  Scalar control_freq_hz = kDefaultSampleFreqHz;
  bool hold_integral_on_saturation = true;
};

class pid {
 public:
  using Gains = pid_gains;
  using Config = pid_config;

  static pid Build(const Config& config) { return pid(config); }

  static pid Build(Scalar k,
                   Scalar p,
                   Scalar i,
                   Scalar d,
                   Scalar output_limit = kUnlimited,
                   Scalar integral_output_limit = kUnlimited,
                   Scalar derivative_cutoff_hz = 0.0f,
                   Scalar control_freq_hz = kDefaultSampleFreqHz) {
    return Build({k, p, i, d}, SymmetricLimit::Abs(output_limit),
                 SymmetricLimit::Abs(integral_output_limit),
                 SymmetricLimit::Unlimited(),
                 RangeWrap::Disabled(), DerivativeMode::kOnMeasurement,
                 derivative_cutoff_hz, true, control_freq_hz);
  }

  static pid Build(const Gains& gains,
                   SymmetricLimit output_limit = SymmetricLimit::Unlimited(),
                   SymmetricLimit integral_output_limit =
                       SymmetricLimit::Unlimited(),
                   SymmetricLimit output_rate_limit =
                       SymmetricLimit::Unlimited(),
                   RangeWrap error_wrap = RangeWrap::Disabled(),
                   DerivativeMode derivative_mode =
                       DerivativeMode::kOnMeasurement,
                   Scalar derivative_cutoff_hz = 0.0f,
                   bool hold_integral_on_saturation = true,
                   Scalar control_freq_hz = kDefaultSampleFreqHz) {
    Config config{};
    config.gains = gains;
    config.output_limit = output_limit;
    config.integral_output_limit = integral_output_limit;
    config.output_rate_limit = output_rate_limit;
    config.error_wrap = error_wrap;
    config.derivative_mode = derivative_mode;
    config.derivative_cutoff_hz = derivative_cutoff_hz;
    config.control_freq_hz = control_freq_hz;
    config.hold_integral_on_saturation = hold_integral_on_saturation;
    return pid(config);
  }

  pid() { Configure(Config{}); }
  explicit pid(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    default_dt_ =
        (IsUsableScalar(config_.control_freq_hz) &&
         config_.control_freq_hz > 0.0f)
            ? 1.0f / config_.control_freq_hz
            : kDefaultDt;
    dfilter_ = mr::comp::filter::low_pass::Build(
        config_.derivative_cutoff_hz, config_.control_freq_hz);
    Reset();
  }

  void Reset(Scalar output = 0.0f) {
    integral_ = 0.0f;
    last_error_ = 0.0f;
    last_k_feedback_ = 0.0f;
    output_limiter_ =
        SlewRateLimiter::Build(config_.output_rate_limit.value, output);
    last_ = {};
    last_.output = output;
    dfilter_.Reset(0.0f);
  }

  void ResetIntegral(Scalar integral_output = 0.0f) {
    if (config_.gains.i > kPidSigma) {
      integral_ = config_.integral_output_limit.Apply(integral_output) /
                  config_.gains.i;
    } else {
      integral_ = 0.0f;
    }
  }

  Scalar Update(Scalar setpoint, Scalar feedback) {
    return Step(setpoint, feedback).output;
  }

  Scalar Update(Scalar setpoint, Scalar feedback, Scalar dt_s) {
    return Step(setpoint, feedback, 0.0f, dt_s).output;
  }

  Scalar Update(Scalar setpoint,
                Scalar feedback,
                Scalar feedback_dot,
                Scalar dt_s) {
    return Step(setpoint, feedback, feedback_dot, dt_s).output;
  }

  Scalar Apply(Scalar setpoint, Scalar feedback) {
    return Update(setpoint, feedback);
  }

  Scalar Apply(Scalar setpoint, Scalar feedback, Scalar dt_s) {
    return Update(setpoint, feedback, dt_s);
  }

  Scalar Apply(Scalar setpoint,
               Scalar feedback,
               Scalar feedback_dot,
               Scalar dt_s) {
    return Update(setpoint, feedback, feedback_dot, dt_s);
  }

  ::mr::comp::cntlr::Step Step(Scalar setpoint, Scalar feedback) {
    return Step(setpoint, feedback, 0.0f, default_dt_);
  }

  ::mr::comp::cntlr::Step Step(Scalar setpoint,
                              Scalar feedback,
                              Scalar dt_s) {
    return Step(setpoint, feedback, 0.0f, dt_s);
  }

  ::mr::comp::cntlr::Step Step(Scalar setpoint,
                              Scalar feedback,
                              Scalar feedback_dot,
                              Scalar dt_s) {
    if (!IsUsableScalar(setpoint) || !IsUsableScalar(feedback) ||
        !IsUsableScalar(feedback_dot)) {
      last_.valid = false;
      return last_;
    }

    const Scalar dt = SanitizeDt(dt_s, default_dt_);
    const Scalar error = config_.error_wrap.Error(setpoint, feedback);

    const Scalar k_error = error * config_.gains.k;
    const Scalar k_feedback = feedback * config_.gains.k;
    const Scalar filtered_k_feedback =
        dfilter_.Update(k_feedback, dt);

    const Scalar p_term = k_error * config_.gains.p;
    const Scalar d_term =
        CalcDerivativeTerm(filtered_k_feedback, feedback_dot, dt);

    const Scalar candidate_integral = integral_ + k_error * dt;
    const Scalar candidate_i_term = candidate_integral * config_.gains.i;
    const Scalar limited_candidate_i_term =
        config_.integral_output_limit.Apply(candidate_i_term);
    const Scalar unsat_with_candidate =
        p_term + limited_candidate_i_term + d_term;
    const Scalar saturated_candidate =
        config_.output_limit.Apply(unsat_with_candidate);

    const bool saturated =
        config_.output_limit.enabled() &&
        mr::component::math::abs_scalar(saturated_candidate -
                                            unsat_with_candidate) > kEpsilon;
    if (config_.gains.i > kPidSigma && IsUsableScalar(candidate_integral)) {
      const bool integral_output_within_limit =
          !config_.integral_output_limit.enabled() ||
          mr::component::math::abs_scalar(candidate_i_term) <=
              config_.integral_output_limit.value;
      if (!config_.hold_integral_on_saturation ||
          (integral_output_within_limit && !saturated)) {
        integral_ = limited_candidate_i_term / config_.gains.i;
      }
    }

    const Scalar i_term = limited_candidate_i_term;
    const Scalar unsat_output = p_term + i_term + d_term;
    Scalar output = config_.output_limit.Apply(unsat_output);
    output = output_limiter_.Update(output, dt);

    last_error_ = error;
    last_k_feedback_ = filtered_k_feedback;
    last_ = {};
    last_.output = output;
    last_.setpoint = setpoint;
    last_.feedback = feedback;
    last_.error = error;
    last_.feedforward = 0.0f;
    last_.p = p_term;
    last_.i = i_term;
    last_.d = d_term;
    last_.valid = true;
    last_.saturated =
        saturated ||
        (mr::component::math::abs_scalar(output - unsat_output) > kEpsilon);
    return last_;
  }

  const ::mr::comp::cntlr::Step& last() const { return last_; }
  const Config& config() const { return config_; }
  Scalar integral() const { return integral_; }

 private:
  static constexpr Scalar kPidSigma = 1.0e-6f;

  Scalar CalcDerivativeTerm(Scalar filtered_k_feedback,
                            Scalar feedback_dot,
                            Scalar dt) {
    Scalar derivative_value = 0.0f;
    switch (config_.derivative_mode) {
      case DerivativeMode::kNone:
        derivative_value = 0.0f;
        break;
      case DerivativeMode::kExternal:
        derivative_value = feedback_dot;
        break;
      case DerivativeMode::kOnMeasurement:
      default:
        derivative_value = (filtered_k_feedback - last_k_feedback_) / dt;
        break;
    }

    if (!IsUsableScalar(derivative_value)) {
      derivative_value = 0.0f;
    }
    return -config_.gains.d * derivative_value;
  }

  Config config_{};
  Scalar default_dt_ = kDefaultDt;
  Scalar integral_ = 0.0f;
  Scalar last_error_ = 0.0f;
  Scalar last_k_feedback_ = 0.0f;
  mr::comp::filter::low_pass dfilter_{};
  SlewRateLimiter output_limiter_{};
  ::mr::comp::cntlr::Step last_{};
};

}  // namespace mr::comp::cntlr
