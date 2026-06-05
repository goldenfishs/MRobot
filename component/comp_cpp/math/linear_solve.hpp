/**
 ******************************************************************************
 * @file    linear_solve.hpp
 * @brief   Linear equation solver using LDL^T decomposition for symmetric
 *          positive definite matrices. 对称正定矩阵线性方程组求解器
 * @author  XuMing Yuan
 ******************************************************************************
 */

#pragma once

#include <stdint.h>

#include "scalar.hpp"
#include "../toolbox/matrix.h"

namespace mr::component::math {

constexpr Scalar kDefaultMinPivot = 1.0e-8f;

template <int Rows, int Cols>
inline bool is_matrix_finite(const Matrixf<Rows, Cols>& matrix) {
  for (uint16_t row = 0; row < Rows; ++row) {
    for (uint16_t col = 0; col < Cols; ++col) {
      if (!is_finite_scalar(matrix[row][col])) {
        return false;
      }
    }
  }
  return true;
}

template <int N, int C>
inline bool solve_symmetric_ldlt(const Matrixf<N, N>& a,
                                 const Matrixf<N, C>& b,
                                 Matrixf<N, C>* x,
                                 Scalar min_pivot = kDefaultMinPivot) {
  if (x == nullptr) {
    return false;
  }

  Matrixf<N, N> l = matrixf::zeros<N, N>();
  Scalar d[N];

  for (uint16_t i = 0; i < N; ++i) {
    d[i] = 0.0f;
    l[i][i] = 1.0f;
  }

  for (uint16_t i = 0; i < N; ++i) {
    for (uint16_t j = 0; j < i; ++j) {
      Scalar sum = a[i][j];
      for (uint16_t k = 0; k < j; ++k) {
        sum -= l[i][k] * d[k] * l[j][k];
      }
      if (abs_scalar(d[j]) <= min_pivot) {
        *x = matrixf::zeros<N, C>();
        return false;
      }
      l[i][j] = sum / d[j];
    }

    Scalar diag = a[i][i];
    for (uint16_t k = 0; k < i; ++k) {
      diag -= l[i][k] * l[i][k] * d[k];
    }
    if (diag <= min_pivot || !is_finite_scalar(diag)) {
      *x = matrixf::zeros<N, C>();
      return false;
    }
    d[i] = diag;
  }

  Matrixf<N, C> y = matrixf::zeros<N, C>();
  for (uint16_t col = 0; col < C; ++col) {
    for (uint16_t i = 0; i < N; ++i) {
      Scalar sum = b[i][col];
      for (uint16_t k = 0; k < i; ++k) {
        sum -= l[i][k] * y[k][col];
      }
      y[i][col] = sum;
    }
  }

  Matrixf<N, C> z = matrixf::zeros<N, C>();
  for (uint16_t col = 0; col < C; ++col) {
    for (uint16_t i = 0; i < N; ++i) {
      z[i][col] = y[i][col] / d[i];
    }
  }

  Matrixf<N, C> out = matrixf::zeros<N, C>();
  for (uint16_t col = 0; col < C; ++col) {
    for (int i = N - 1; i >= 0; --i) {
      Scalar sum = z[i][col];
      for (uint16_t k = static_cast<uint16_t>(i + 1); k < N; ++k) {
        sum -= l[k][i] * out[k][col];
      }
      out[i][col] = sum;
    }
  }

  if (!is_matrix_finite(out)) {
    *x = matrixf::zeros<N, C>();
    return false;
  }

  *x = out;
  return true;
}

template <int N>
inline bool solve_symmetric_ldlt(const Matrixf<N, N>& a,
                                 const Matrixf<N, 1>& b,
                                 Matrixf<N, 1>* x,
                                 Scalar min_pivot = kDefaultMinPivot) {
  return solve_symmetric_ldlt<N, 1>(a, b, x, min_pivot);
}

}  // namespace mr::component::math
