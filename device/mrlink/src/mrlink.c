/**
  ******************************************************************************
  * @file    mrlink.c
  * @brief   通用 byte-stream frame 协议实现 / Generic frame protocol impl.
  ******************************************************************************
  */

#define MRLINK_INTERNAL_BUILD
#include "mrlink/mrlink.h"
#include <string.h>

#include "cmsis_compiler.h"   /**< __disable_irq / __enable_irq / __get_PRIMASK */
#include "component/crc16.h"

/* Private types ------------------------------------------------------------ */

_Static_assert(sizeof(MrLink_t) <= MRLINK_INSTANCE_STORAGE_SIZE,
               "MRLINK_INSTANCE_STORAGE_SIZE is too small");

/* Private function prototypes --------------------------------------------- */

static int8_t Proto_ProcessRx(MrLink_t *p, bool want_one_frame,
                              uint8_t *out_cmd,
                              const uint8_t **out_payload,
                              uint16_t *out_payload_len);
static void Proto_ReportError(MrLink_t *p, const MrLink_ErrorInfo_t *info);

/* Private functions -------------------------------------------------------- */

static void Proto_ReportError(MrLink_t *p, const MrLink_ErrorInfo_t *info) {
  if (p == NULL || info == NULL || p->error_handler == NULL) {
    return;
  }
  p->error_handler(info, p->error_ctx);
}

/**
 * @brief 扫描 ring buffer 中所有可解析的字节，处理有效帧。
 *
 * @details 控制律 / Control law (滑动窗口 6 步):
 *   while offset < n:
 *     1. 帧头检查: buf[offset..+2] == {0x4D, 0x52}?
 *        否: offset += 1, 统计 frame_rx_header_skip, 跳回 1
 *     2. 长度校验: length (buf[+2]) > max_payload_size?
 *        是: offset += 2, 统计 frame_rx_oversize, 跳回 1
 *     3. 完整性: n - offset >= total (含 CRC)?
 *        否: 统计 frame_rx_truncated, break (等下次喂入)
 *     4. CRC (若 use_crc16): 计算 vs buf[total-2..total-1]
 *        错: offset += 1, 统计 frame_rx_crc_err, 跳回 1
 *     5. 查表派发:
 *        typed: 校验 size, memcpy 到 frame_buf, 调 typed handler
 *        raw  : 调 raw handler (业务 memcpy)
 *        未订阅: 统计 frame_rx_unknown_cmd
 *     6. 消费: offset += total, 统计 frame_rx_ok
 *   最后: 丢弃 [0..offset] 所有字节
 *
 * @return want_one_frame 模式下: MRLINK_OK 或 MRLINK_ERR
 *         其他模式: MRLINK_OK
 */
static int8_t Proto_ProcessRx(MrLink_t *p, bool want_one_frame,
                              uint8_t *out_cmd,
                              const uint8_t **out_payload,
                              uint16_t *out_payload_len) {
  const uint16_t avail = SpscRingBuf_Size(&p->rx_rb);
  if (avail == 0u) {
    return MRLINK_ERR;
  }

  /* Peek 局部缓冲 (frame 上限 70 字节, 栈空间足够) */
  uint8_t buf[MRLINK_MAX_FRAME_SIZE];
  const uint16_t to_peek =
      (avail > MRLINK_MAX_FRAME_SIZE) ? MRLINK_MAX_FRAME_SIZE : avail;
  const uint16_t n = SpscRingBuf_Peek(&p->rx_rb, buf, to_peek);

  bool found_one = false;
  uint16_t offset = 0u;

  while (offset < n) {
    /* 1. 帧头检查 */
    if ((uint16_t)(n - offset) < MRLINK_HEADER_LEN) {
      break;
    }
    if (buf[offset] != MRLINK_HEADER_0 ||
        buf[offset + 1u] != MRLINK_HEADER_1) {
      offset = (uint16_t)(offset + 1u);
      p->stats.frame_rx_header_skip++;
      const MrLink_ErrorInfo_t info = {
          .code = MRLINK_ERROR_HEADER_SKIP,
          .available = n,
      };
      Proto_ReportError(p, &info);
      continue;
    }

    /* 2. length 字段 */
    if ((uint16_t)(n - offset) <
        MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN) {
      break;
    }
    const uint8_t length = buf[offset + 2u];
    if (length > p->cfg.max_payload_size) {
      offset = (uint16_t)(offset + MRLINK_HEADER_LEN);
      p->stats.frame_rx_oversize++;
      const MrLink_ErrorInfo_t info = {
          .code = MRLINK_ERROR_OVERSIZE,
          .payload_len = length,
          .expected_size = p->cfg.max_payload_size,
          .available = n,
      };
      Proto_ReportError(p, &info);
      continue;
    }

    /* 3. 计算总帧长, 检查完整性 */
    const uint16_t total = (uint16_t)(
        MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
        MRLINK_CMD_FIELD_LEN + length +
        (p->cfg.use_crc16 ? MRLINK_CRC_LEN : 0u));
    if ((uint16_t)(n - offset) < total) {
      p->stats.frame_rx_truncated++;
      const MrLink_ErrorInfo_t info = {
          .code = MRLINK_ERROR_TRUNCATED,
          .payload_len = length,
          .expected_size = total,
          .available = (uint16_t)(n - offset),
      };
      Proto_ReportError(p, &info);
      break;  /* 等下次喂入更多数据 */
    }

    /* 4. CRC 校验 (可选) */
    if (p->cfg.use_crc16) {
      const uint16_t crc_recv =
          (uint16_t)buf[offset + total - 2u] |
          ((uint16_t)buf[offset + total - 1u] << 8);
      const uint16_t crc_calc =
          CRC16_Calc(&buf[offset], (size_t)(total - MRLINK_CRC_LEN),
                     CRC16_INIT);
      if (crc_recv != crc_calc) {
        offset = (uint16_t)(offset + 1u);  /* 滑窗 1 字节 */
        p->stats.frame_rx_crc_err++;
        const MrLink_ErrorInfo_t info = {
            .code = MRLINK_ERROR_CRC,
            .payload_len = length,
            .available = n,
            .crc_received = crc_recv,
            .crc_calculated = crc_calc,
        };
        Proto_ReportError(p, &info);
        continue;
      }
    }

    /* 5. 有效帧: 查表派发 handler / 填出参 */
    const uint8_t cmd = buf[offset + 3u];
    const uint8_t *payload = &buf[offset + 4u];

    uint8_t found_idx = 0xFFu;
    for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
      if (p->handlers[i].used && p->handlers[i].cmd == cmd) {
        found_idx = i;
        break;
      }
    }
    if (found_idx == 0xFFu) {
      p->stats.frame_rx_unknown_cmd++;
      const MrLink_ErrorInfo_t info = {
          .code = MRLINK_ERROR_UNKNOWN_CMD,
          .cmd = cmd,
          .payload_len = length,
          .available = n,
      };
      Proto_ReportError(p, &info);
    } else if (p->handlers[found_idx].expected_size > 0u) {
      /* typed handler: 库校验长度, memcpy 到内部缓冲 */
      if (length != p->handlers[found_idx].expected_size) {
        p->stats.frame_rx_size_mismatch++;
        const MrLink_ErrorInfo_t info = {
            .code = MRLINK_ERROR_SIZE_MISMATCH,
            .cmd = cmd,
            .payload_len = length,
            .expected_size = p->handlers[found_idx].expected_size,
            .available = n,
        };
        Proto_ReportError(p, &info);
        offset = (uint16_t)(offset + total);
        continue;
      }
      memcpy(p->frame_buf, payload, length);
      (void)p->handlers[found_idx].handler.typed(
          cmd, p->frame_buf, length, p->handlers[found_idx].ctx);
    } else if (p->handlers[found_idx].handler.raw != NULL) {
      /* raw handler: 业务自行处理 payload */
      (void)p->handlers[found_idx].handler.raw(
          cmd, payload, length, p->handlers[found_idx].ctx);
    }

    if (want_one_frame && !found_one) {
      if (length > 0u) {
        memcpy(p->frame_buf, payload, length);
      }
      *out_cmd = cmd;
      *out_payload = p->frame_buf;
      *out_payload_len = length;
      found_one = true;
    }

    p->stats.frame_rx_ok++;
    offset = (uint16_t)(offset + total);
  }

  /* 丢弃已消费的字节 (offset 之前的所有字节) */
  if (offset > 0u) {
    (void)SpscRingBuf_Drop(&p->rx_rb, offset);
  }

  if (want_one_frame) {
    return found_one ? MRLINK_OK : MRLINK_ERR;
  }
  return MRLINK_OK;
}

/* Exported functions ------------------------------------------------------- */

/**
 * @brief 初始化协议实例.
 *
 * @details 控制律 / Control law (5 步):
 *   1. 指针非空检查 (p / rx_buf / tx_buf)
 *   2. 应用配置: 默认 + cfg 覆盖
 *   3. 范围校验: max_payload_size ∈ [1, 255]
 *   4. 计算 max_frame, 验证 rx_buf_size >= max_frame && tx_buf_size >= max_frame
 *   5. 初始化 ring buffer + 清空 handlers + 清空 stats
 *
 * 设计意图: rx_buf 装不下完整一帧时 parser 永远 truncated,
 *           tx_buf 装不下完整一帧时 Build 永远失败, 故提前报错.
 */
int8_t MrLink_Init(MrLink_t *p, const MrLink_Config_t *cfg,
                       uint8_t *rx_buf, uint16_t rx_buf_size,
                       uint8_t *tx_buf, uint16_t tx_buf_size) {
  if (p == NULL || rx_buf == NULL || tx_buf == NULL) {
    return MRLINK_ERR_NULL;
  }

  /* 应用配置 (默认 + 覆盖) */
  MrLink_Config_t applied = {
      .max_payload_size = MRLINK_MAX_PAYLOAD_DEFAULT,
      .use_crc16 = true,
  };
  if (cfg != NULL) {
    applied = *cfg;
  }

  /* 计算当前配置下的最大帧长, 验证 rx/tx 缓冲足够装下完整一帧。
   * 否则 parser 会永久 truncated (rx_buf) 或 Build 永远失败 (tx_buf). */
  const uint16_t max_frame = MrLink_MaxFrameSizeForConfig(&applied);
  if (max_frame == 0u) {
    return MRLINK_ERR_ARGS;
  }
  if (rx_buf_size < max_frame) {
    return MRLINK_ERR_ARGS;
  }
  if (tx_buf_size < max_frame) {
    return MRLINK_ERR_ARGS;
  }

  const int8_t ret = SpscRingBuf_Init(&p->rx_rb, rx_buf, rx_buf_size);
  if (ret != SPSC_RINGBUF_OK) {
    return MRLINK_ERR_ARGS;
  }

  p->cfg = applied;
  p->rx_buf = rx_buf;
  p->rx_buf_size = rx_buf_size;
  p->tx_buf = tx_buf;
  p->tx_buf_size = tx_buf_size;
  memset(p->handlers, 0, sizeof(p->handlers));
  memset(&p->stats, 0, sizeof(p->stats));
  p->error_handler = NULL;
  p->error_ctx = NULL;

  return MRLINK_OK;
}

uint16_t MrLink_MaxFrameSizeForConfig(const MrLink_Config_t *cfg) {
  MrLink_Config_t applied = {
      .max_payload_size = MRLINK_MAX_PAYLOAD_DEFAULT,
      .use_crc16 = true,
  };
  if (cfg != NULL) {
    applied = *cfg;
  }

  if (applied.max_payload_size == 0u ||
      applied.max_payload_size > MRLINK_MAX_PAYLOAD_DEFAULT) {
    return 0u;
  }

  return (uint16_t)(MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
                    MRLINK_CMD_FIELD_LEN + applied.max_payload_size +
                    (applied.use_crc16 ? MRLINK_CRC_LEN : 0u));
}

/**
 * @brief 复位协议实例.
 *
 * @details 控制律 / Control law (3 步):
 *   1. ring buffer Reset (head/tail = 0, 旧数据丢弃)
 *   2. 清空所有 32 槽 handler (used=false, handler=NULL)
 *   3. 清空所有 stats 计数器
 *   注意: 不释放 rx/tx 缓冲 (用户管理), 不调 ISR 通知
 */
void MrLink_Reset(MrLink_t *p) {
  if (p == NULL) {
    return;
  }
  SpscRingBuf_Reset(&p->rx_rb);
  memset(p->handlers, 0, sizeof(p->handlers));
  memset(&p->stats, 0, sizeof(p->stats));
}

/**
 * @brief 喂入 RX 字节流, 自动解析 + 派发.
 *
 * @details 控制律 / Control law (3 步):
 *   1. 边界: 指针非空, len>0 时 data 非空
 *   2. 写入 ring buffer (Put, 满了截断, 返回实际写入数)
 *   3. 调 Proto_ProcessRx 扫描所有可解析字节, 自动派发 handler
 *
 * 两种用法:
 *   - 纯回调模式: 注册 handler → FeedBytes (ISR/任务) 自动派发
 *   - 拉取模式: 不注册 handler → FeedBytes (ISR) → MrLink_Parse (任务)
 * ISR/任务上下文均可调用 (ring buffer Put 用 PRIMASK 临界区互斥)
 */
int8_t MrLink_PushBytes(MrLink_t *p, const uint8_t *data, uint16_t len) {
  if (p == NULL || (data == NULL && len > 0u)) {
    return MRLINK_ERR_ARGS;
  }
  if (len == 0u) {
    p->stats.feed_calls++;
    return MRLINK_OK;
  }

  const uint16_t written = SpscRingBuf_Put(&p->rx_rb, data, len);
  p->stats.feed_bytes_total += written;
  p->stats.feed_bytes_dropped += (uint32_t)(len - written);
  p->stats.feed_calls++;
  if (written < len) {
    const MrLink_ErrorInfo_t info = {
        .code = MRLINK_ERROR_RX_DROPPED,
        .available = written,
        .dropped_bytes = (uint16_t)(len - written),
    };
    Proto_ReportError(p, &info);
  }

  return MRLINK_OK;
}

int8_t MrLink_Dispatch(MrLink_t *p) {
  if (p == NULL) {
    return MRLINK_ERR_NULL;
  }

  const uint32_t prev_frame_rx_ok = p->stats.frame_rx_ok;
  const int8_t ret = Proto_ProcessRx(p, false, NULL, NULL, NULL);
  if (ret != MRLINK_OK) {
    return ret;
  }
  return (p->stats.frame_rx_ok != prev_frame_rx_ok) ? MRLINK_OK : MRLINK_ERR;
}

int8_t MrLink_FeedBytes(MrLink_t *p, const uint8_t *data, uint16_t len) {
  const int8_t ret = MrLink_PushBytes(p, data, len);
  if (ret != MRLINK_OK) {
    return ret;
  }

  /* Backward-compatible behavior: push and immediately dispatch handlers. */
  (void)MrLink_Dispatch(p);
  return MRLINK_OK;
}

/**
 * @brief 拉取一帧 (拉取模式, 任务上下文).
 *
 * @details 控制律 / Control law (1 步委托):
 *   调 Proto_ProcessRx(want_one_frame=true)
 *     - 找到: 写 *out_cmd / *out_payload / *out_payload_len, 返回 MRLINK_OK
 *     - 无完整帧: 返回 MRLINK_ERR
 *   注意: payload 指针指向实例内 frame_buf, 下次 Parse/Feed 前有效。
 *   配合: ISR 里 FeedBytes, 任务里循环 Parse (适用于不注册 handler 的场景)
 */
int8_t MrLink_Parse(MrLink_t *p, uint8_t *out_cmd,
                        const uint8_t **out_payload,
                        uint16_t *out_payload_len) {
  if (p == NULL || out_cmd == NULL || out_payload == NULL ||
      out_payload_len == NULL) {
    return MRLINK_ERR_NULL;
  }
  return Proto_ProcessRx(p, true, out_cmd, out_payload, out_payload_len);
}

/**
 * @brief 构造一帧写入 tx_buf.
 *
 * @details 控制律 / Control law (5 步):
 *   1. 边界: 指针非空, payload_len <= max_payload_size,
 *      payload_len>0 时 payload 非空
 *   2. 计算 total = 2 (header) + 1 (len) + 1 (cmd) + payload_len + [2 (CRC)]
 *   3. 验证 tx_buf_size >= total
 *   4. 写入: header(0x4D,0x52) → len → cmd → payload
 *   5. (use_crc16) 算 CRC16-CCITT-FALSE (init=0xFFFF, poly=0x1021) → 写 2B 小端
 * 返回: 实际写入字节数 (含 header/CRC); 失败返回 0
 */
uint16_t MrLink_Build(MrLink_t *p, uint8_t cmd,
                          const uint8_t *payload, uint16_t payload_len) {
  if (p == NULL) {
    return 0u;
  }
  if (payload_len > p->cfg.max_payload_size) {
    return 0u;
  }
  if (payload_len > 0u && payload == NULL) {
    return 0u;
  }

  const uint16_t total = (uint16_t)(
      MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
      MRLINK_CMD_FIELD_LEN + payload_len +
      (p->cfg.use_crc16 ? MRLINK_CRC_LEN : 0u));
  if (p->tx_buf_size < total) {
    return 0u;
  }

  uint8_t *b = p->tx_buf;
  uint16_t idx = 0u;

  b[idx++] = MRLINK_HEADER_0;
  b[idx++] = MRLINK_HEADER_1;
  b[idx++] = (uint8_t)payload_len;
  b[idx++] = cmd;
  if (payload_len > 0u) {
    memcpy(&b[idx], payload, payload_len);
    idx = (uint16_t)(idx + payload_len);
  }

  if (p->cfg.use_crc16) {
    const uint16_t crc = CRC16_Calc(b, idx, CRC16_INIT);
    b[idx++] = (uint8_t)(crc & 0xFFu);
    b[idx++] = (uint8_t)((crc >> 8u) & 0xFFu);
  }

  p->stats.frame_tx_ok++;
  return idx;
}

/**
 * @brief 注册 raw cmd handler (业务自己处理 payload).
 *
 * @details 控制律 / Control law (3 段式, 32 槽线性扫表):
 *   - handler = NULL: 注销. 扫表找 used && cmd 匹配, 清空
 *   - 覆盖: 扫表找 used && cmd 匹配, 直接替换 (expected_size=0 标记 raw)
 *   - 插入: 扫表找 !used 空槽, 填 used=true / cmd / raw handler / ctx
 *   - 表满 (32 槽都用): 返回 MRLINK_ERR_ARGS
 * 时间: 最坏 O(32) ≈ 32 次比较
 * 业务侧收到 `(cmd, payload, len, ctx)`, 需自己 memcpy payload
 */
int8_t MrLink_RegisterHandler(MrLink_t *p, uint8_t cmd,
                                  MrLink_FrameHandler_t handler,
                                  void *ctx) {
  if (p == NULL) {
    return MRLINK_ERR_NULL;
  }

  /* 注销: handler = NULL */
  if (handler == NULL) {
    for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
      if (p->handlers[i].used && p->handlers[i].cmd == cmd) {
        p->handlers[i].used = false;
        p->handlers[i].cmd = 0u;
        p->handlers[i].expected_size = 0u;
        p->handlers[i].handler.raw = NULL;
        p->handlers[i].ctx = NULL;
        return MRLINK_OK;
      }
    }
    return MRLINK_ERR_ARGS;  /* 该 cmd 未注册过 */
  }

  /* 覆盖: 同 cmd 已有 handler, 直接替换 (raw) */
  for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
    if (p->handlers[i].used && p->handlers[i].cmd == cmd) {
      p->handlers[i].expected_size = 0u;
      p->handlers[i].handler.raw = handler;
      p->handlers[i].ctx = ctx;
      return MRLINK_OK;
    }
  }

  /* 插入: 找空槽 (raw) */
  for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
    if (!p->handlers[i].used) {
      p->handlers[i].used = true;
      p->handlers[i].cmd = cmd;
      p->handlers[i].expected_size = 0u;
      p->handlers[i].handler.raw = handler;
      p->handlers[i].ctx = ctx;
      return MRLINK_OK;
    }
  }

  return MRLINK_ERR_ARGS;  /* 表满 */
}

/**
 * @brief 注册 typed cmd handler (库做 length check + memcpy).
 *
 * @details 控制律 / Control law (3 段式, 同 RegisterHandler):
 *   - handler = NULL: 注销
 *   - 覆盖: 替换 (expected_size=N 标记 typed)
 *   - 插入: 找空槽
 *   - 校验: expected_size ∈ [1, max_payload_size]
 *
 * 派发时 (在 Proto_ProcessRx):
 *   - length == expected_size: memcpy 到 p->frame_buf, 调 typed handler
 *   - length != expected_size: 统计 frame_rx_size_mismatch, 消费完整坏帧
 * 业务侧收到 `(cmd, const void* data, size, ctx)`, data 指向 frame_buf
 */
int8_t MrLink_RegisterTypedHandler(MrLink_t *p, uint8_t cmd,
                                       uint16_t expected_size,
                                       MrLink_TypedHandler_t handler,
                                       void *ctx) {
  if (p == NULL) {
    return MRLINK_ERR_NULL;
  }
  if (expected_size == 0u || expected_size > p->cfg.max_payload_size) {
    return MRLINK_ERR_ARGS;
  }

  /* 注销: handler = NULL */
  if (handler == NULL) {
    for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
      if (p->handlers[i].used && p->handlers[i].cmd == cmd) {
        p->handlers[i].used = false;
        p->handlers[i].cmd = 0u;
        p->handlers[i].expected_size = 0u;
        p->handlers[i].handler.typed = NULL;
        p->handlers[i].ctx = NULL;
        return MRLINK_OK;
      }
    }
    return MRLINK_ERR_ARGS;
  }

  /* 覆盖: 同 cmd 已有, 替换为 typed */
  for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
    if (p->handlers[i].used && p->handlers[i].cmd == cmd) {
      p->handlers[i].expected_size = expected_size;
      p->handlers[i].handler.typed = handler;
      p->handlers[i].ctx = ctx;
      return MRLINK_OK;
    }
  }

  /* 插入: 找空槽 (typed) */
  for (uint8_t i = 0u; i < MRLINK_MAX_HANDLERS; i++) {
    if (!p->handlers[i].used) {
      p->handlers[i].used = true;
      p->handlers[i].cmd = cmd;
      p->handlers[i].expected_size = expected_size;
      p->handlers[i].handler.typed = handler;
      p->handlers[i].ctx = ctx;
      return MRLINK_OK;
    }
  }

  return MRLINK_ERR_ARGS;  /* 表满 */
}

int8_t MrLink_SetErrorHandler(MrLink_t *p,
                              MrLink_ErrorHandler_t handler,
                              void *ctx) {
  if (p == NULL) {
    return MRLINK_ERR_NULL;
  }
  p->error_handler = handler;
  p->error_ctx = ctx;
  return MRLINK_OK;
}

/**
 * @brief 获取 stats 指针 (只读, 常驻).
 *
 * @details 控制律 / Control law (1 步):
 *   - p == NULL: 返回 NULL
 *   - 否则: 返回 &p->stats (指向实例内部)
 * 注意: 返回的指针生命周期与实例一致; 跨实例操作前请确认 p 仍有效
 */
const MrLink_Stats_t *MrLink_GetStats(const MrLink_t *p) {
  if (p == NULL) {
    return NULL;
  }
  return &p->stats;
}

uint32_t MrLink_EnterCritical(void) {
  const uint32_t primask = __get_PRIMASK();
  __disable_irq();
  return primask;
}

void MrLink_ExitCritical(uint32_t primask) {
  if (primask == 0u) {
    __enable_irq();
  }
}
