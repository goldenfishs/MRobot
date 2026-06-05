#pragma once

/*
 * 通用扩展 Kalman 滤波器。
 *
 * 适用于非线性离散系统：
 *
 *   x(k) = f(x(k-1), u(k)) + w
 *   z(k) = h(x(k)) + v
 *
 * 用户需要提供 f、df/dx、h、dh/dx 四个函数。这样 EKF 本身只负责预测、
 * 线性化后的协方差传播，以及测量修正。
 *
 * 模板参数：
 *   StateDim   : 状态向量维度
 *   MeasureDim : 测量向量维度
 *   ControlDim : 控制输入维度，默认 1；无控制输入时直接调用 Predict()
 *
 * 最小用法：
 *
 *   using Filter = mr::comp::filter::ekf<2, 1, 1>;
 *
 *   bool Transition(const Filter::State& x,
 *                   const Filter::Control& u,
 *                   Filter::State* out,
 *                   void* context);
 *   bool TransitionJacobian(const Filter::State& x,
 *                           const Filter::Control& u,
 *                           Filter::StateTransition* out,
 *                           void* context);
 *   bool Observation(const Filter::State& x,
 *                    Filter::Measurement* out,
 *                    void* context);
 *   bool ObservationJacobian(const Filter::State& x,
 *                            Filter::Observation* out,
 *                            void* context);
 *
 *   Filter::Config cfg;
 *   cfg.transition = Transition;
 *   cfg.transition_jacobian = TransitionJacobian;
 *   cfg.observation = Observation;
 *   cfg.observation_jacobian = ObservationJacobian;
 *   cfg.Q[0][0] = 0.01f;
 *   cfg.R[0][0] = 0.10f;
 *
 *   auto filter = Filter::Build(cfg);
 *   filter.Step(u, z);
 *
 * 更新步内部使用 component/math/linear_solve.hpp 的 LDLT 解线性方程，
 * 不显式计算 S 的逆矩阵。协方差默认使用 Joseph 形式更新，数值上更稳。
 */

#include <stdint.h>

#include "component/filter/filter_types.hpp"
#include "component/math/linear_solve.hpp"

namespace mr::comp::filter {

template <int StateDim, int MeasureDim, int ControlDim = 1>
class ekf {
  static_assert(StateDim > 0, "ekf needs at least one state");
  static_assert(MeasureDim > 0, "ekf needs at least one measurement");
  static_assert(ControlDim > 0, "ekf ControlDim must be positive");

 public:
  using State = Matrixf<StateDim, 1>;
  using Measurement = Matrixf<MeasureDim, 1>;
  using Control = Matrixf<ControlDim, 1>;
  using StateTransition = Matrixf<StateDim, StateDim>;
  using Observation = Matrixf<MeasureDim, StateDim>;
  using StateCovariance = Matrixf<StateDim, StateDim>;
  using MeasurementCovariance = Matrixf<MeasureDim, MeasureDim>;
  using InnovationCovariance = Matrixf<MeasureDim, MeasureDim>;
  using Gain = Matrixf<StateDim, MeasureDim>;

  using TransitionFunction =
      bool (*)(const State& state,
               const Control& control,
               State* out,
               void* context);
  using TransitionJacobianFunction =
      bool (*)(const State& state,
               const Control& control,
               StateTransition* out,
               void* context);
  using ObservationFunction =
      bool (*)(const State& state, Measurement* out, void* context);
  using ObservationJacobianFunction =
      bool (*)(const State& state, Observation* out, void* context);

  struct Config {
    TransitionFunction transition;
    TransitionJacobianFunction transition_jacobian;
    ObservationFunction observation;
    ObservationJacobianFunction observation_jacobian;
    void* context;
    StateCovariance Q;
    MeasurementCovariance R;
    StateCovariance P0;
    State x0;
    Scalar min_pivot;
    bool joseph_covariance_update;

    Config()
        : transition(nullptr),
          transition_jacobian(nullptr),
          observation(nullptr),
          observation_jacobian(nullptr),
          context(nullptr),
          Q(matrixf::zeros<StateDim, StateDim>()),
          R(matrixf::eye<MeasureDim, MeasureDim>()),
          P0(matrixf::eye<StateDim, StateDim>()),
          x0(matrixf::zeros<StateDim, 1>()),
          min_pivot(mr::component::math::kDefaultMinPivot),
          joseph_covariance_update(true) {}
  };

  static ekf Build(const Config& config) { return ekf(config); }

  ekf() { Configure(Config{}); }
  explicit ekf(const Config& config) { Configure(config); }

  void Configure(const Config& config) {
    config_ = config;
    if (!mr::component::math::is_positive_scalar(config_.min_pivot)) {
      config_.min_pivot = mr::component::math::kDefaultMinPivot;
    }
    Reset(config_.x0, config_.P0);
  }

  void Reset() { Reset(config_.x0, config_.P0); }

  void Reset(const State& x0) { Reset(x0, config_.P0); }

  void Reset(const State& x0, const StateCovariance& P0) {
    x_ = x0;
    P_ = Symmetrized(P0);
    F_ = matrixf::eye<StateDim, StateDim>();
    H_ = matrixf::zeros<MeasureDim, StateDim>();
    K_ = matrixf::zeros<StateDim, MeasureDim>();
    predicted_measurement_ = matrixf::zeros<MeasureDim, 1>();
    innovation_ = matrixf::zeros<MeasureDim, 1>();
    innovation_covariance_ = matrixf::zeros<MeasureDim, MeasureDim>();
    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_);
  }

  bool Predict() {
    const Control zero_control = matrixf::zeros<ControlDim, 1>();
    return Predict(zero_control);
  }

  bool Predict(const Control& control) {
    if (!valid_ || !IsPredictModelUsable() ||
        !mr::component::math::is_matrix_finite(control)) {
      valid_ = false;
      return false;
    }

    State predicted = matrixf::zeros<StateDim, 1>();
    StateTransition transition_jacobian =
        matrixf::zeros<StateDim, StateDim>();
    if (!config_.transition(x_, control, &predicted, config_.context) ||
        !config_.transition_jacobian(x_, control, &transition_jacobian,
                                     config_.context)) {
      valid_ = false;
      return false;
    }
    if (!IsStateUsable(predicted) ||
        !mr::component::math::is_matrix_finite(transition_jacobian)) {
      valid_ = false;
      return false;
    }

    F_ = transition_jacobian;
    x_ = predicted;
    P_ = Symmetrized(F_ * P_ * F_.trans() + config_.Q);
    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_);
    return valid_;
  }

  bool Update(const Measurement& measurement) {
    if (!valid_ || !IsUpdateModelUsable() ||
        !mr::component::math::is_matrix_finite(measurement)) {
      valid_ = false;
      return false;
    }

    Measurement predicted_measurement = matrixf::zeros<MeasureDim, 1>();
    Observation observation_jacobian =
        matrixf::zeros<MeasureDim, StateDim>();
    if (!config_.observation(x_, &predicted_measurement, config_.context) ||
        !config_.observation_jacobian(x_, &observation_jacobian,
                                      config_.context)) {
      valid_ = false;
      return false;
    }
    if (!mr::component::math::is_matrix_finite(predicted_measurement) ||
        !mr::component::math::is_matrix_finite(observation_jacobian)) {
      valid_ = false;
      return false;
    }

    predicted_measurement_ = predicted_measurement;
    H_ = observation_jacobian;

    const Matrixf<StateDim, MeasureDim> pht = P_ * H_.trans();
    innovation_ = measurement - predicted_measurement_;
    innovation_covariance_ = Symmetrized(H_ * pht + config_.R);

    Matrixf<MeasureDim, StateDim> kt = matrixf::zeros<MeasureDim, StateDim>();
    if (!mr::component::math::solve_symmetric_ldlt<MeasureDim, StateDim>(
            innovation_covariance_, pht.trans(), &kt, config_.min_pivot)) {
      valid_ = false;
      return false;
    }

    K_ = kt.trans();
    x_ = x_ + K_ * innovation_;
    UpdateCorrectedCovariance();

    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_) &&
             mr::component::math::is_matrix_finite(K_);
    return valid_;
  }

  bool Step(const Measurement& measurement) {
    return Predict() && Update(measurement);
  }

  bool Step(const Control& control, const Measurement& measurement) {
    return Predict(control) && Update(measurement);
  }

  const Config& config() const { return config_; }
  const State& state() const { return x_; }
  const StateCovariance& covariance() const { return P_; }
  const StateTransition& transition_jacobian() const { return F_; }
  const Observation& observation_jacobian() const { return H_; }
  const Gain& gain() const { return K_; }
  const Measurement& predicted_measurement() const {
    return predicted_measurement_;
  }
  const Measurement& innovation() const { return innovation_; }
  const InnovationCovariance& innovation_covariance() const {
    return innovation_covariance_;
  }
  bool valid() const { return valid_; }

 private:
  template <int N>
  static Matrixf<N, N> Symmetrized(const Matrixf<N, N>& matrix) {
    return 0.5f * (matrix + matrix.trans());
  }

  static bool IsStateUsable(const State& state) {
    return mr::component::math::is_matrix_finite(state);
  }

  static bool IsStateCovarianceUsable(const StateCovariance& covariance) {
    return mr::component::math::is_matrix_finite(covariance);
  }

  bool IsPredictModelUsable() const {
    return config_.transition != nullptr &&
           config_.transition_jacobian != nullptr &&
           mr::component::math::is_matrix_finite(config_.Q);
  }

  bool IsUpdateModelUsable() const {
    return config_.observation != nullptr &&
           config_.observation_jacobian != nullptr &&
           mr::component::math::is_matrix_finite(config_.R);
  }

  void UpdateCorrectedCovariance() {
    const StateCovariance identity = matrixf::eye<StateDim, StateDim>();
    const StateCovariance ikh = identity - K_ * H_;

    if (config_.joseph_covariance_update) {
      P_ = Symmetrized(ikh * P_ * ikh.trans() +
                       K_ * config_.R * K_.trans());
    } else {
      P_ = Symmetrized(ikh * P_);
    }
  }

  Config config_{};
  State x_ = matrixf::zeros<StateDim, 1>();
  StateCovariance P_ = matrixf::eye<StateDim, StateDim>();
  StateTransition F_ = matrixf::eye<StateDim, StateDim>();
  Observation H_ = matrixf::zeros<MeasureDim, StateDim>();
  Gain K_ = matrixf::zeros<StateDim, MeasureDim>();
  Measurement predicted_measurement_ = matrixf::zeros<MeasureDim, 1>();
  Measurement innovation_ = matrixf::zeros<MeasureDim, 1>();
  InnovationCovariance innovation_covariance_ =
      matrixf::zeros<MeasureDim, MeasureDim>();
  bool valid_ = false;
};

}  // namespace mr::comp::filter
