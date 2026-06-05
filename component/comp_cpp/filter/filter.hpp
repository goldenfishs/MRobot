#pragma once

/*
 * C++ 滤波器组件聚合头文件。
 *
 * 模块需要同时使用多种滤波器时，直接包含这个头文件：
 *
 *   #include "component/filter/filter.hpp"
 *
 *   auto lp = mr::comp::filter::low_pass::Build(30.0f, 1000.0f);
 *   auto hp = mr::comp::filter::high_pass::Build(2.0f, 1000.0f);
 *   auto nt = mr::comp::filter::notch::Build(50.0f, 5.0f, 1000.0f);
 *
 *   using Kf1D = mr::comp::filter::kf<1, 1>;
 *   Kf1D::Config cfg;
 *   cfg.Q[0][0] = 0.01f;
 *   cfg.R[0][0] = 0.10f;
 *   auto kf = Kf1D::Build(cfg);
 *
 *   using Ekf = mr::comp::filter::ekf<2, 1, 1>;
 *   Ekf::Config ekf_cfg;
 *   ekf_cfg.transition = Transition;
 *   ekf_cfg.transition_jacobian = TransitionJacobian;
 *   ekf_cfg.observation = Observation;
 *   ekf_cfg.observation_jacobian = ObservationJacobian;
 *   auto ekf = Ekf::Build(ekf_cfg);
 */

#include "component/filter/filter_types.hpp"
#include "component/filter/ekf.hpp"
#include "component/filter/high_pass_filter.hpp"
#include "component/filter/kf.hpp"
#include "component/filter/low_pass_filter.hpp"
#include "component/filter/notch_filter.hpp"
