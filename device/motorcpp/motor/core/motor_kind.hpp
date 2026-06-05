#pragma once

// 定义电机厂商/协议类别枚举。
// 当前用于区分 RM / DM / LZ 三条协议链路。

#include <stdint.h>

namespace mr::motor {

enum class MotorKind : uint8_t {
    RM = 0,
    DM = 1,
    LZ = 2,
};

} // namespace mr::motor