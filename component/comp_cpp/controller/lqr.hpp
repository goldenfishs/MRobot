/*
 * 通用 LQR 状态反馈控制器
 *
 * 类型形式:
 *   mr::comp::cntlr::lqr<StateDim, ControlDim = 1, PolyOrder = 1>
 *
 * 模板参数:
 *   StateDim   : 状态量数量, 例如 [theta, d_theta, x, d_x, phi, d_phi] 是 6
 *   ControlDim : 控制输出数量, 例如 [轮毂力矩 T, 髋关节力矩 Tp] 是 2
 *   PolyOrder  : 每个增益 K 的多项式系数数量
 *                PolyOrder = 1 表示固定 LQR
 *                PolyOrder = 4 表示三次多项式调度 LQR
 *
 * 控制律:
 *   error = state - reference
 *   u = feedforward - K * error
 *  
 * api:
 * 固定 LQR 示例:
 *   using Lqr = mr::comp::cntlr::lqr<6, 2>;
 *
 *   Lqr::Config cfg{};
 *   cfg.coeff[0][0][0] = k11;  // 第 0 个输出对第 0 个状态的固定增益
 *   cfg.coeff[0][1][0] = k12;
 *   ...
 *   cfg.coeff[1][5][0] = k26;  // 第 1 个输出对第 5 个状态的固定增益
 *   cfg.output_limit[0] = mr::comp::cntlr::SymmetricLimit::Abs(10.0f);
 *   cfg.output_limit[1] = mr::comp::cntlr::SymmetricLimit::Abs(8.0f);
 *d1222
 *   auto ctrl = Lqr::Build(cfg);
 *   Lqr::State ref = {0.0f, 0.0f, target_x, target_v, 0.0f, 0.0f};
 *   Lqr::State x = {theta, d_theta, pos_x, vel_x, pitch, pitch_rate};
 *   Lqr::Control u = ctrl.Update(ref, x);
 *   float T = u[0];
 *   float Tp = u[1];
 *
 * 多项式增益调度 LQR 示例:
 *   using Lqr = mr::comp::cntlr::lqr<6, 2, 4>;
 *
 *   Lqr::Config cfg{};
 *   cfg.schedule_min = 0.10f;
 *   cfg.schedule_max = 0.40f;
 *   cfg.coeff[0][0] = {a, b, c, d};  // K00(s) = a*s^3 + b*s^2 + c*s + d
 *   cfg.coeff[1][5] = {a, b, c, d};
 *
 *   auto ctrl = Lqr::Build(cfg);
 *   ctrl.UpdateSchedule(leg_length);  // 根据腿长等调度量更新当前 K
 *   Lqr::Control u = ctrl.Update(ref, x);
 *
 * 参数说明
 *   coeff[control][state][poly]
 *     control : 第几个控制输出
 *     state   : 第几个状态误差
 *     poly    : 多项式系数索引, 按高次到低次排列
 *
 *   output_limit[i]
 *     第 i 个控制输出的对称限幅。值为 0 表示不限幅。
 *
 *   state_wrap[i]
 *     第 i 个状态的周期误差处理。角度状态可设置为:
 *       mr::comp::cntlr::RangeWrap::Periodic(2.0f * pi)
 *
 *   schedule_min / schedule_max
 *     调度量限幅。clamp_schedule 为 true 时生效。
 *
 *   feedforward
 *     可选前馈控制量。调用 Update(ref, state, feedforward) 时使用。
 */

#pragma once

#include <array>
#include <stdint.h>

#include "component/controller/controller_types.hpp"

namespace mr::comp::cntlr {

template <uint16_t StateDim, uint16_t ControlDim = 1, uint16_t PolyOrder = 1>
class lqr {
  static_assert(StateDim > 0U, "lqr needs at least one state");
  static_assert(ControlDim > 0U, "lqr needs at least one control output");
  static_assert(PolyOrder > 0U, "lqr needs at least one gain coefficient");

 public:
  using State = std::array<Scalar, StateDim>;
  using Control = std::array<Scalar, ControlDim>;
  using Gain = std::array<std::array<Scalar, StateDim>, ControlDim>;
  using Coeff =
      std::array<std::array<std::array<Scalar, PolyOrder>, StateDim>,
                 ControlDim>;
  using OutputLimit = std::array<SymmetricLimit, ControlDim>;
  using StateWrap = std::array<RangeWrap, StateDim>;

  struct Config {
    Coeff coeff{};
    OutputLimit output_limit{};
    StateWrap state_wrap{};
    Scalar schedule_min = kUnlimited;
    Scalar schedule_max = kUnlimited;
    bool clamp_schedule = true;
  };

  struct Step {
    State error{};
    Control feedforward{};
    Control unsaturated_output{};
    Control output{};
    std::array<bool, ControlDim> channel_saturated{};
    bool valid = false;
    bool saturated = false;
  };

  static lqr Build(const Config& config) { return lqr(config); }

  lqr() { Configure(Config{}); }
  explicit lqr(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    Reset();
    current_schedule_ = 0.0f;
    if constexpr (PolyOrder == 1U) {
      RecalculateGain(0.0f);
      schedule_valid_ = true;
    } else {
      gain_ = {};
      schedule_valid_ = false;
    }
  }

  void Reset() { last_ = {}; }

  void SetCoeff(const Coeff& coeff) {
    config_.coeff = coeff;
    if constexpr (PolyOrder == 1U) {
      RecalculateGain(0.0f);
      schedule_valid_ = true;
    } else if (schedule_valid_) {
      RecalculateGain(current_schedule_);
    }
  }

  bool UpdateSchedule(Scalar schedule) {
    if (!IsUsableScalar(schedule)) {
      schedule_valid_ = false;
      return false;
    }

    schedule = ClampSchedule(schedule);
    RecalculateGain(schedule);
    current_schedule_ = schedule;
    schedule_valid_ = true;
    return true;
  }

  void SetOutputLimit(uint16_t index, SymmetricLimit limit) {
    if (index < ControlDim) {
      config_.output_limit[index] = limit;
    }
  }

  void SetStateWrap(uint16_t index, RangeWrap wrap) {
    if (index < StateDim) {
      config_.state_wrap[index] = wrap;
    }
  }

  Control Update(const State& reference, const State& state) {
    return StepOnce(reference, state).output;
  }

  Control Update(const State& reference,
                 const State& state,
                 const Control& feedforward) {
    return StepOnce(reference, state, feedforward).output;
  }

  Control UpdateError(const State& error) {
    return StepError(error).output;
  }

  Control UpdateError(const State& error, const Control& feedforward) {
    return StepError(error, feedforward).output;
  }

  Step StepOnce(const State& reference, const State& state) {
    return StepOnce(reference, state, ZeroControl());
  }

  Step StepOnce(const State& reference,
                const State& state,
                const Control& feedforward) {
    State error{};
    if (!BuildError(reference, state, &error)) {
      last_ = {};
      return last_;
    }
    return StepError(error, feedforward);
  }

  Step StepError(const State& error) {
    return StepError(error, ZeroControl());
  }

  Step StepError(const State& error, const Control& feedforward) {
    last_ = {};
    last_.error = error;
    last_.feedforward = feedforward;

    if (!schedule_valid_ || !IsStateUsable(error) ||
        !IsControlUsable(feedforward)) {
      return last_;
    }

    for (uint16_t output = 0; output < ControlDim; ++output) {
      Scalar value = feedforward[output];
      for (uint16_t state = 0; state < StateDim; ++state) {
        value -= gain_[output][state] * error[state];
      }

      last_.unsaturated_output[output] = value;
      last_.output[output] = config_.output_limit[output].Apply(value);
      last_.channel_saturated[output] =
          mr::component::math::abs_scalar(last_.output[output] - value) >
          kEpsilon;
      last_.saturated = last_.saturated || last_.channel_saturated[output];
    }

    last_.valid = true;
    return last_;
  }

  const Config& config() const { return config_; }
  const Gain& gain() const { return gain_; }
  const Step& last() const { return last_; }
  Scalar current_schedule() const { return current_schedule_; }
  bool schedule_valid() const { return schedule_valid_; }

 private:
  static constexpr Control ZeroControl() { return Control{}; }

  static bool IsStateUsable(const State& value) {
    for (uint16_t i = 0; i < StateDim; ++i) {
      if (!IsUsableScalar(value[i])) {
        return false;
      }
    }
    return true;
  }

  static bool IsControlUsable(const Control& value) {
    for (uint16_t i = 0; i < ControlDim; ++i) {
      if (!IsUsableScalar(value[i])) {
        return false;
      }
    }
    return true;
  }

  bool BuildError(const State& reference,
                  const State& state,
                  State* error) const {
    if (error == nullptr || !IsStateUsable(reference) ||
        !IsStateUsable(state)) {
      return false;
    }

    for (uint16_t i = 0; i < StateDim; ++i) {
      (*error)[i] = config_.state_wrap[i].Error(state[i], reference[i]);
    }
    return true;
  }

  Scalar ClampSchedule(Scalar schedule) const {
    if (!config_.clamp_schedule) {
      return schedule;
    }
    if (IsUsableScalar(config_.schedule_min) &&
        IsUsableScalar(config_.schedule_max) &&
        config_.schedule_max > config_.schedule_min) {
      return mr::component::math::clamp_scalar(
          schedule, config_.schedule_min, config_.schedule_max);
    }
    return schedule;
  }

  void RecalculateGain(Scalar schedule) {
    for (uint16_t output = 0; output < ControlDim; ++output) {
      for (uint16_t state = 0; state < StateDim; ++state) {
        gain_[output][state] =
            EvalPolynomial(config_.coeff[output][state], schedule);
      }
    }
  }

  static Scalar EvalPolynomial(const std::array<Scalar, PolyOrder>& coeff,
                               Scalar schedule) {
    Scalar value = 0.0f;
    for (uint16_t i = 0; i < PolyOrder; ++i) {
      value = value * schedule + coeff[i];
    }
    return value;
  }

  Config config_{};
  Gain gain_{};
  Step last_{};
  Scalar current_schedule_ = 0.0f;
  bool schedule_valid_ = false;
};

}  // namespace mr::comp::cntlr
