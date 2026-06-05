#pragma once

// 定义电机安装信息。
// 用于描述机构侧附加传动比与输出方向翻转，供协议层完成输出端物理量换算。

#include <stdbool.h>

namespace mr::motor {

struct MotorInstallSpec {
    // 机构额外传动比，定义为：电机输出轴角 / 机构最终输出角。无额外传动时填 1.0f。
    float external_ratio;
    // 保留配置字段兼容旧参数；方向反转统一使用 MotorInstanceConfig::reverse。
    bool reverse_output;
};

inline constexpr MotorInstallSpec kDirectDriveInstall {
    1.0f,
    false,
};

} // namespace mr::motor