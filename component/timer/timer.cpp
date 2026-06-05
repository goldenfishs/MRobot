/*
 * 用法总结：
 *
 *   #include "component/timer.hpp"
 *
 *   auto loop_timer = mr::comp::timer::Build(1.0f / CTRL_FREQ);
 *
 *   while (1) {
 *     const float dt_s = loop_timer.Update();
 *     control.Update(dt_s);
 *   }
 *
 * 常用操作：
 *   loop_timer.Update()       -> 返回本次循环 dt，单位：秒
 *   loop_timer.UpdateUs()     -> 返回本次循环 dt，单位：微秒
 *   loop_timer.ElapsedMs()    -> 从首次 Reset/Update 后经过的时间
 *   loop_timer.SinceUpdateS() -> 距离上次 Update 经过的时间
 *   loop_timer.EveryMs(100)   -> 非阻塞 100 ms 周期触发
 *   loop_timer.ExpiredMs(500) -> 判断是否已超时 500 ms
 *
 * 注意：
 *   - 默认时钟源是 BSP_TIME_Get_us()。
 *   - 构造对象时不会读取硬件时钟，第一次调用 Update()、Reset() 或
 *     Every*() 时才启动计时。
 *   - Build(first_dt_s, min_dt_s, max_dt_s) 可设置第一次 dt，并限制异常
 *     循环间隔。
 */
#include "component/timer.hpp"

#include "bsp/time.h"

namespace mr::comp {

namespace {

constexpr uint64_t kUsPerMs = 1000U;
constexpr uint64_t kUsPerS = 1000000U;

ClockUsFn ResolveClock(ClockUsFn clock_us) {
  return (clock_us != nullptr) ? clock_us : DefaultClockUs;
}

uint64_t MsToUs(uint32_t milliseconds) {
  return static_cast<uint64_t>(milliseconds) * kUsPerMs;
}

}  // namespace

uint64_t DefaultClockUs() {
  return BSP_TIME_Get_us();
}

timer::timer() {
  Configure(Config{});
}

timer::timer(const Config& config) {
  Configure(config);
}

void timer::Configure(const Config& config) {
  config_ = config;
  config_.clock_us = ResolveClock(config_.clock_us);
  if (config_.max_dt_us > 0U && config_.min_dt_us > config_.max_dt_us) {
    config_.min_dt_us = config_.max_dt_us;
  }

  start_us_ = 0U;
  last_update_us_ = 0U;
  period_anchor_us_ = 0U;
  last_dt_us_ = 0U;
  started_ = false;
}

uint64_t timer::UpdateUs() {
  const uint64_t now_us = NowUs();
  uint64_t dt_us = config_.first_dt_us;

  if (started_) {
    dt_us = now_us - last_update_us_;
    last_update_us_ = now_us;
  } else {
    Reset(now_us);
  }

  last_dt_us_ = ClampDt(dt_us);
  return last_dt_us_;
}

uint32_t timer::UpdateMs() {
  return UsToMs(UpdateUs());
}

float timer::Update() {
  return UsToSeconds(UpdateUs());
}

void timer::Reset() {
  Reset(NowUs());
}

void timer::Reset(uint64_t now_us) {
  start_us_ = now_us;
  last_update_us_ = now_us;
  period_anchor_us_ = now_us;
  last_dt_us_ = 0U;
  started_ = true;
}

void timer::ResetPeriod() {
  ResetPeriod(NowUs());
}

void timer::ResetPeriod(uint64_t now_us) {
  if (!started_) {
    start_us_ = now_us;
    last_update_us_ = now_us;
    started_ = true;
  }
  period_anchor_us_ = now_us;
}

uint64_t timer::NowUs() const {
  return ResolveClock(config_.clock_us)();
}

uint64_t timer::ElapsedUs() const {
  if (!started_) {
    return 0U;
  }
  return NowUs() - start_us_;
}

uint32_t timer::ElapsedMs() const {
  return UsToMs(ElapsedUs());
}

float timer::ElapsedS() const {
  return UsToSeconds(ElapsedUs());
}

uint64_t timer::SinceUpdateUs() const {
  if (!started_) {
    return 0U;
  }
  return NowUs() - last_update_us_;
}

uint32_t timer::SinceUpdateMs() const {
  return UsToMs(SinceUpdateUs());
}

float timer::SinceUpdateS() const {
  return UsToSeconds(SinceUpdateUs());
}

void timer::SetPeriodUs(uint64_t period_us) {
  config_.period_us = period_us;
}

void timer::SetPeriodMs(uint32_t period_ms) {
  SetPeriodUs(MsToUs(period_ms));
}

void timer::SetPeriodS(float period_s) {
  SetPeriodUs(SecondsToUs(period_s));
}

bool timer::Expired() const {
  return ExpiredUs(config_.period_us);
}

bool timer::ExpiredUs(uint64_t period_us) const {
  return PeriodElapsed(period_us, NowUs());
}

bool timer::ExpiredMs(uint32_t period_ms) const {
  return ExpiredUs(MsToUs(period_ms));
}

bool timer::ExpiredS(float period_s) const {
  return ExpiredUs(SecondsToUs(period_s));
}

bool timer::Every() {
  return EveryUs(config_.period_us);
}

bool timer::EveryUs(uint64_t period_us) {
  if (period_us == 0U) {
    return false;
  }

  const uint64_t now_us = NowUs();
  if (!started_) {
    Reset(now_us);
    return false;
  }

  const uint64_t elapsed_us = now_us - period_anchor_us_;
  if (elapsed_us < period_us) {
    return false;
  }

  const uint64_t periods = elapsed_us / period_us;
  period_anchor_us_ += periods * period_us;
  return true;
}

bool timer::EveryMs(uint32_t period_ms) {
  return EveryUs(MsToUs(period_ms));
}

bool timer::EveryS(float period_s) {
  return EveryUs(SecondsToUs(period_s));
}

uint64_t timer::SecondsToUs(float seconds) {
  if (!(seconds > 0.0f)) {
    return 0U;
  }
  constexpr float kMaxSeconds =
      static_cast<float>(UINT64_MAX) / static_cast<float>(kUsPerS);
  if (seconds >= kMaxSeconds) {
    return UINT64_MAX;
  }
  return static_cast<uint64_t>(seconds * static_cast<float>(kUsPerS) + 0.5f);
}

float timer::UsToSeconds(uint64_t us) {
  return static_cast<float>(us) / static_cast<float>(kUsPerS);
}

uint32_t timer::UsToMs(uint64_t us) {
  const uint64_t ms = us / kUsPerMs;
  return (ms > UINT32_MAX) ? UINT32_MAX : static_cast<uint32_t>(ms);
}

uint64_t timer::ClampDt(uint64_t dt_us) const {
  uint64_t out = dt_us;
  if (config_.min_dt_us > 0U && out < config_.min_dt_us) {
    out = config_.min_dt_us;
  }
  if (config_.max_dt_us > 0U && out > config_.max_dt_us) {
    out = config_.max_dt_us;
  }
  return out;
}

bool timer::PeriodElapsed(uint64_t period_us, uint64_t now_us) const {
  if (!started_ || period_us == 0U) {
    return false;
  }
  return (now_us - period_anchor_us_) >= period_us;
}

}  // namespace mr::comp
