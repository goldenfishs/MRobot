#pragma once

// motor 模块总入口。
// 默认导出强类型体系：MotorKind / MotorModel / Traits / Config / MotorT / aliases。
// 主路径不再依赖旧 runtime 抽象，仅保留当前仍有用途的静态工厂与类型别名入口。

#include "device/motor/core/motor_capability.hpp"
#include "device/motor/core/motor_instance_config.hpp"
#include "device/motor/core/motor_kind.hpp"
#include "device/motor/core/motor_model.hpp"
#include "device/motor/core/motor_aliases.hpp"
#include "device/motor/core/motor_state.hpp"
#include "device/motor/core/motor_t.hpp"
#include "device/motor/core/motor_traits.hpp"
