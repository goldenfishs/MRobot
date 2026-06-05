#pragma once

// 定义电机支持的控制能力位标志。
// 用于在编译期/运行期判断是否支持电流、速度、位置、MIT 等控制方式。

#include <stdint.h>

namespace mr::motor {

enum class MotorCapability : uint32_t {
    None = 0,
    Current = 1u << 0,
    Velocity = 1u << 1,
    Position = 1u << 2,
    MIT = 1u << 3,
};

inline constexpr MotorCapability operator|(MotorCapability lhs, MotorCapability rhs) {
    return static_cast<MotorCapability>(static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

inline constexpr MotorCapability operator&(MotorCapability lhs, MotorCapability rhs) {
    return static_cast<MotorCapability>(static_cast<uint32_t>(lhs) & static_cast<uint32_t>(rhs));
}

inline constexpr bool HasCapability(MotorCapability caps, MotorCapability cap) {
    return static_cast<uint32_t>(caps & cap) != 0u;
}

} // namespace mr::motor
