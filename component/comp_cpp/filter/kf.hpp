#pragma once

/*
 * 通用线性 Kalman 滤波器。
 *
 * 适用于线性离散系统：
 *
 *   x(k) = A * x(k-1) + B * u(k) + w
 *   z(k) = H * x(k) + v
 *
 * 模板参数：
 *   StateDim   : 状态向量维度
 *   MeasureDim : 测量向量维度
 *   ControlDim : 控制输入维度，默认 1；无控制输入时直接调用 Predict()
 *
 * 一维直接测量示例：
 *
 *   using Filter = mr::comp::filter::kf<1, 1>;
 *
 *   Filter::Config cfg;
 *   cfg.Q[0][0] = 0.01f;  // 过程噪声协方差
 *   cfg.R[0][0] = 0.10f;  // 测量噪声协方差
 *   cfg.P0[0][0] = 1.0f;  // 初始估计协方差
 *
 *   auto filter = Filter::Build(cfg);
 *   Filter::Measurement z = matrixf::zeros<1, 1>();
 *   z[0][0] = measurement;
 *   filter.Step(z);
 *   float y = filter.state()[0][0];
 *
 * 有控制输入时：
 *
 *   Filter::Control u = matrixf::zeros<1, 1>();
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
class kf {
  static_assert(StateDim > 0, "kf needs at least one state");
  static_assert(MeasureDim > 0, "kf needs at least one measurement");
  static_assert(ControlDim > 0, "kf ControlDim must be positive");

 public:
  using State = Matrixf<StateDim, 1>;
  using Measurement = Matrixf<MeasureDim, 1>;
  using Control = Matrixf<ControlDim, 1>;
  using StateTransition = Matrixf<StateDim, StateDim>;
  using ControlMatrix = Matrixf<StateDim, ControlDim>;
  using Observation = Matrixf<MeasureDim, StateDim>;
  using StateCovariance = Matrixf<StateDim, StateDim>;
  using MeasurementCovariance = Matrixf<MeasureDim, MeasureDim>;
  using InnovationCovariance = Matrixf<MeasureDim, MeasureDim>;
  using Gain = Matrixf<StateDim, MeasureDim>;

  struct Config {
    StateTransition A;
    ControlMatrix B;
    Observation H;
    StateCovariance Q;
    MeasurementCovariance R;
    StateCovariance P0;
    State x0;
    Scalar min_pivot;
    bool joseph_covariance_update;

    Config()
        : A(matrixf::eye<StateDim, StateDim>()),
          B(matrixf::zeros<StateDim, ControlDim>()),
          H(matrixf::zeros<MeasureDim, StateDim>()),
          Q(matrixf::zeros<StateDim, StateDim>()),
          R(matrixf::eye<MeasureDim, MeasureDim>()),
          P0(matrixf::eye<StateDim, StateDim>()),
          x0(matrixf::zeros<StateDim, 1>()),
          min_pivot(mr::component::math::kDefaultMinPivot),
          joseph_covariance_update(true) {
      const uint16_t diag_count =
          (StateDim < MeasureDim) ? StateDim : MeasureDim;
      for (uint16_t i = 0; i < diag_count; ++i) {
        H[i][i] = 1.0f;
      }
    }
  };

  static kf Build(const Config& config) { return kf(config); }

  kf() { Configure(Config{}); }
  explicit kf(const Config& config) { Configure(config); }

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
    K_ = matrixf::zeros<StateDim, MeasureDim>();
    innovation_ = matrixf::zeros<MeasureDim, 1>();
    innovation_covariance_ = matrixf::zeros<MeasureDim, MeasureDim>();
    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_);
  }

  bool Predict() {
    if (!valid_ || !IsPredictModelUsable()) {
      valid_ = false;
      return false;
    }

    x_ = config_.A * x_;
    UpdatePredictedCovariance();
    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_);
    return valid_;
  }

  bool Predict(const Control& control) {
    if (!valid_ || !IsPredictModelUsable() ||
        !mr::component::math::is_matrix_finite(control)) {
      valid_ = false;
      return false;
    }

    x_ = config_.A * x_ + config_.B * control;
    UpdatePredictedCovariance();
    valid_ = IsStateUsable(x_) && IsStateCovarianceUsable(P_);
    return valid_;
  }

  bool Update(const Measurement& measurement) {
    if (!valid_ || !IsUpdateModelUsable() ||
        !mr::component::math::is_matrix_finite(measurement)) {
      valid_ = false;
      return false;
    }

    const Matrixf<StateDim, MeasureDim> pht = P_ * config_.H.trans();
    innovation_ = measurement - config_.H * x_;
    innovation_covariance_ =
        Symmetrized(config_.H * pht + config_.R);

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
  const Gain& gain() const { return K_; }
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
    return mr::component::math::is_matrix_finite(config_.A) &&
           mr::component::math::is_matrix_finite(config_.B) &&
           mr::component::math::is_matrix_finite(config_.Q);
  }

  bool IsUpdateModelUsable() const {
    return mr::component::math::is_matrix_finite(config_.H) &&
           mr::component::math::is_matrix_finite(config_.R);
  }

  void UpdatePredictedCovariance() {
    P_ = Symmetrized(config_.A * P_ * config_.A.trans() + config_.Q);
  }

  void UpdateCorrectedCovariance() {
    const StateCovariance identity = matrixf::eye<StateDim, StateDim>();
    const StateCovariance ikh = identity - K_ * config_.H;

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
  Gain K_ = matrixf::zeros<StateDim, MeasureDim>();
  Measurement innovation_ = matrixf::zeros<MeasureDim, 1>();
  InnovationCovariance innovation_covariance_ =
      matrixf::zeros<MeasureDim, MeasureDim>();
  bool valid_ = false;
};

}  // namespace mr::comp::filter
