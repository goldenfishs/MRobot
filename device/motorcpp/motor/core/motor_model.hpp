#pragma once

// 定义电机型号枚举，作为强类型 motor 体系中的型号维度。
// 与 MotorKind 组合后，用于 Traits / Protocol / MotorT 的编译期分发。

#include <stdint.h>

namespace mr::motor {

enum class MotorModel : uint16_t {
    Unknown = 0,

    M2006,
    M3508,
    M6020,

    J10010,
    J10010L,
    J10422P,
    J3507,
    J4310,
    J4310P,
    J4340,
    J4340P,
    J6006,
    J6248P,
    J8006,
    J8009,
    J8009P,
    H3510,

    RSO0,
    RSO1,
    RSO2,
    RSO3,
    RSO4,
    RSO5,
    RSO6,
};

} // namespace mr::motor