#pragma once

// 定义协议层待提交命令类型。
// 用于缓存 SetXXX 请求，并在 CommitCommand 中统一下发到底层驱动。

#include <stdint.h>

namespace mr::motor {

enum class PendingCommandType : uint8_t {
    None = 0,
    Velocity,
    Position,
    Mit,
};

} // namespace mr::motor