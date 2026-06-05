#pragma once

#include <stdint.h>

namespace mr::comp {

using ClockUsFn = uint64_t (*)();

uint64_t DefaultClockUs();

struct timer_config {
  ClockUsFn clock_us = DefaultClockUs;
  uint64_t first_dt_us = 0U;
  uint64_t min_dt_us = 0U;
  uint64_t max_dt_us = 0U;
  uint64_t period_us = 0U;
};

class timer final {
 public:
  using Config = timer_config;

  static timer Build() { return timer(Config{}); }
  static timer Build(const Config& config) { return timer(config); }
  static timer Build(float first_dt_s,
                     float min_dt_s = 0.0f,
                     float max_dt_s = 0.0f) {
    Config config{};
    config.first_dt_us = SecondsToUs(first_dt_s);
    config.min_dt_us = SecondsToUs(min_dt_s);
    config.max_dt_us = SecondsToUs(max_dt_s);
    return timer(config);
  }

  timer();
  explicit timer(const Config& config);

  void Configure(const Config& config);
  const Config& config() const { return config_; }

  uint64_t UpdateUs();
  uint32_t UpdateMs();
  float Update();

  uint64_t TickUs() { return UpdateUs(); }
  uint32_t TickMs() { return UpdateMs(); }
  float TickS() { return Update(); }

  void Reset();
  void Reset(uint64_t now_us);
  void ResetPeriod();
  void ResetPeriod(uint64_t now_us);

  uint64_t NowUs() const;
  uint64_t ElapsedUs() const;
  uint32_t ElapsedMs() const;
  float ElapsedS() const;
  uint64_t SinceUpdateUs() const;
  uint32_t SinceUpdateMs() const;
  float SinceUpdateS() const;

  void SetPeriodUs(uint64_t period_us);
  void SetPeriodMs(uint32_t period_ms);
  void SetPeriodS(float period_s);
  bool Expired() const;
  bool ExpiredUs(uint64_t period_us) const;
  bool ExpiredMs(uint32_t period_ms) const;
  bool ExpiredS(float period_s) const;
  bool Every();
  bool EveryUs(uint64_t period_us);
  bool EveryMs(uint32_t period_ms);
  bool EveryS(float period_s);

  uint64_t dt_us() const { return last_dt_us_; }
  uint32_t dt_ms() const { return UsToMs(last_dt_us_); }
  float dt_s() const { return UsToSeconds(last_dt_us_); }
  bool started() const { return started_; }

  static uint64_t SecondsToUs(float seconds);
  static float UsToSeconds(uint64_t us);
  static uint32_t UsToMs(uint64_t us);

 private:
  uint64_t ClampDt(uint64_t dt_us) const;
  bool PeriodElapsed(uint64_t period_us, uint64_t now_us) const;

  Config config_{};
  uint64_t start_us_ = 0U;
  uint64_t last_update_us_ = 0U;
  uint64_t period_anchor_us_ = 0U;
  uint64_t last_dt_us_ = 0U;
  bool started_ = false;
};

using Timer = timer;

}  // namespace mr::comp
