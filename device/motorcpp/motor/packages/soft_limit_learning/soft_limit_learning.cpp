#include "device/motor/packages/soft_limit_learning/soft_limit_learning.hpp"

#include "component/math/range_limits.hpp"
#include "component/math/scalar.hpp"

namespace mr::motor {

namespace {

namespace scalar = mr::component::math;

constexpr float kStallVelocityThresholdRadS = SOFT_LIMIT_LEARNING_STALL_VELOCITY_THRESHOLD_RAD_S;
constexpr float kStallPositionWindowRad = SOFT_LIMIT_LEARNING_STALL_POSITION_WINDOW_RAD;
constexpr uint16_t kStallCyclesRequired = SOFT_LIMIT_LEARNING_STALL_CYCLES_REQUIRED;
constexpr float kSeekTimeoutS = SOFT_LIMIT_LEARNING_SEEK_TIMEOUT_S;
constexpr float kSeekStartupIgnoreS = SOFT_LIMIT_LEARNING_SEEK_STARTUP_IGNORE_S;
constexpr float kLearnedLimitMarginRad = SOFT_LIMIT_LEARNING_LEARNED_LIMIT_MARGIN_RAD;

float ClampNonNegative(float value) {
    return (scalar::is_finite_scalar(value) && value > 0.0f) ? value : 0.0f;
}

float ClampFiniteNonNegative(float value, float fallback) {
    if (!scalar::is_finite_scalar(value) || value < 0.0f) {
        return fallback;
    }
    return value;
}

float AbsFloat(float value) {
    return scalar::abs_scalar(value);
}

bool IsFinitePosition(float position_rad) {
    return scalar::is_finite_scalar(position_rad);
}

bool IsFiniteMotorState(const MotorState& state) {
    return scalar::is_finite_scalar(state.position_rad) &&
           scalar::is_finite_scalar(state.velocity_rad_s);
}

bool RangeBoundValuesFinite(const SoftLimitRange& range) {
    if (range.lower_valid && !IsFinitePosition(range.lower_rad)) {
        return false;
    }
    if (range.upper_valid && !IsFinitePosition(range.upper_rad)) {
        return false;
    }
    return true;
}

bool NormalizeRangeCandidate(SoftLimitRange& range, float min_range_rad) {
    if (!RangeBoundValuesFinite(range)) {
        return false;
    }

    if (range.lower_valid && range.upper_valid) {
        if (range.lower_rad > range.upper_rad) {
            const float tmp = range.lower_rad;
            range.lower_rad = range.upper_rad;
            range.upper_rad = tmp;
        }

        const float min_range = ClampNonNegative(min_range_rad);
        if ((range.upper_rad - range.lower_rad) < min_range) {
            return false;
        }
    }
    return true;
}

mr::component::math::RangeLimits<1> BuildRangeLimits(float lower_rad,
                                                     float upper_rad) {
    mr::component::math::RangeLimits<1> limits;
    limits.set(0u, lower_rad, upper_rad);
    return limits;
}

mr::comp::timer::Config BuildObserveTimerConfig() {
    mr::comp::timer::Config timer_config{};
    if (kSeekTimeoutS > 0.0f) {
        timer_config.max_dt_us = mr::comp::timer::SecondsToUs(kSeekTimeoutS);
    }
    return timer_config;
}

} // namespace

SoftLimitLearning::SoftLimitLearning() {
    Configure(config_);
}

SoftLimitLearning::SoftLimitLearning(const SoftLimitLearningConfig& config) {
    Configure(config);
}

void SoftLimitLearning::Configure(const SoftLimitLearningConfig& config) {
    config_ = config;
    config_.seek_velocity_rad_s =
        ClampFiniteNonNegative(config_.seek_velocity_rad_s, 0.0f);
    config_.known_travel_rad =
        ClampFiniteNonNegative(config_.known_travel_rad, 0.0f);
    config_.limit_margin_rad =
        ClampFiniteNonNegative(config_.limit_margin_rad, 0.0f);
    config_.min_range_rad =
        ClampFiniteNonNegative(config_.min_range_rad, 0.0f);
    observe_timer_.Configure(BuildObserveTimerConfig());
    if (!NormalizeRangeCandidate(range_, config_.min_range_rad)) {
        range_ = {};
        if (!IsSeeking()) {
            state_ = SoftLimitLearningState::Idle;
        }
    } else if (!IsSeeking()) {
        state_ = ResolveIdleState();
    }
}

const SoftLimitLearningConfig& SoftLimitLearning::GetConfig() const {
    return config_;
}

void SoftLimitLearning::Reset() {
    range_ = {};
    observed_state_ = {};
    has_observed_state_ = false;
    ResetSeekTracking();
    ClearWorkflow();
    post_learn_target_available_ = false;
    post_learn_target_position_rad_ = 0.0f;
    state_ = SoftLimitLearningState::Idle;
}

void SoftLimitLearning::ResetLearningState() {
    ResetSeekTracking();
    ClearWorkflow();
    state_ = ResolveIdleState();
}

void SoftLimitLearning::ClearRange() {
    range_ = {};
    ResetLearningState();
}

void SoftLimitLearning::Observe(const MotorState& state) {
    Observe(state, observe_timer_.Update());
}

void SoftLimitLearning::Observe(const MotorState& state, float dt_s) {
    observed_state_ = state;
    has_observed_state_ = IsFiniteMotorState(state);

    if (!IsSeeking()) {
        return;
    }

    if (!state.online || !IsFiniteMotorState(state)) {
        stall_cycles_ = 0u;
        seek_position_initialized_ = false;
        return;
    }

    const float dt = ClampFiniteNonNegative(dt_s, 0.0f);
    elapsed_seek_s_ += dt;
    if (kSeekTimeoutS > 0.0f && elapsed_seek_s_ >= kSeekTimeoutS) {
        MarkFailed();
        return;
    }

    if (startup_ignore_left_s_ > 0.0f) {
        startup_ignore_left_s_ -= dt;
        if (startup_ignore_left_s_ < 0.0f) {
            startup_ignore_left_s_ = 0.0f;
        }
        last_seek_position_rad_ = state.position_rad;
        seek_position_initialized_ = true;
        stall_cycles_ = 0u;
        return;
    }

    if (!seek_position_initialized_) {
        last_seek_position_rad_ = state.position_rad;
        seek_position_initialized_ = true;
        return;
    }

    const float position_delta = AbsFloat(state.position_rad - last_seek_position_rad_);
    last_seek_position_rad_ = state.position_rad;

    const bool velocity_small =
        AbsFloat(state.velocity_rad_s) <= kStallVelocityThresholdRadS;
    const bool position_small =
        position_delta <= kStallPositionWindowRad;

    if (velocity_small && position_small) {
        if (stall_cycles_ < UINT16_MAX) {
            ++stall_cycles_;
        }
    } else {
        stall_cycles_ = 0u;
    }

    if (stall_cycles_ >= kStallCyclesRequired) {
        FinishSeekAt(state.position_rad);
    }
}

void SoftLimitLearning::ResetObserverTimer() {
    observe_timer_.Reset();
}

bool SoftLimitLearning::StartSeekLower() {
    return StartSeek(config_.seek_velocity_rad_s, false, SoftLimitLearningWorkflow::SingleLower, 0.0f);
}

bool SoftLimitLearning::StartSeekUpper() {
    return StartSeek(config_.seek_velocity_rad_s, true, SoftLimitLearningWorkflow::SingleUpper, 0.0f);
}

bool SoftLimitLearning::StartSeekLowerWithTravel() {
    if (!scalar::is_finite_scalar(config_.known_travel_rad) || config_.known_travel_rad <= 0.0f) {
        return false;
    }
    return StartSeek(config_.seek_velocity_rad_s, false, SoftLimitLearningWorkflow::LowerWithTravel, config_.known_travel_rad);
}

bool SoftLimitLearning::StartSeekUpperWithTravel() {
    if (!scalar::is_finite_scalar(config_.known_travel_rad) || config_.known_travel_rad <= 0.0f) {
        return false;
    }
    return StartSeek(config_.seek_velocity_rad_s, true, SoftLimitLearningWorkflow::UpperWithTravel, config_.known_travel_rad);
}

bool SoftLimitLearning::StartSeekUpperThenLower() {
    return StartSeek(config_.seek_velocity_rad_s, true, SoftLimitLearningWorkflow::UpperThenLower, 0.0f);
}

bool SoftLimitLearning::StartSeekLowerThenUpper() {
    return StartSeek(config_.seek_velocity_rad_s, false, SoftLimitLearningWorkflow::LowerThenUpper, 0.0f);
}

bool SoftLimitLearning::StartSeek(float seek_velocity_rad_s,
                                  bool upper,
                                  SoftLimitLearningWorkflow workflow,
                                  float travel_rad) {
    const float seek_speed = ClampNonNegative(AbsFloat(seek_velocity_rad_s));
    if (seek_speed <= 0.0f) {
        return false;
    }

    ResetSeekTracking();
    post_learn_target_available_ = false;
    post_learn_target_position_rad_ = 0.0f;
    workflow_ = workflow;
    pending_travel_rad_ = ClampNonNegative(travel_rad);
    pending_seek_speed_rad_s_ = seek_speed;
    seek_velocity_rad_s_ = upper ? seek_speed : -seek_speed;
    state_ = upper ? SoftLimitLearningState::SeekingUpper : SoftLimitLearningState::SeekingLower;
    return true;
}

void SoftLimitLearning::CancelSeek() {
    ResetLearningState();
}

void SoftLimitLearning::MarkFailed() {
    ResetSeekTracking();
    ClearWorkflow();
    state_ = SoftLimitLearningState::Failed;
}

bool SoftLimitLearning::CaptureLower(float position_rad) {
    if (!IsFinitePosition(position_rad)) {
        return false;
    }
    SoftLimitRange candidate = range_;
    candidate.lower_rad = position_rad;
    candidate.lower_valid = true;
    return CommitRange(candidate);
}

bool SoftLimitLearning::CaptureUpper(float position_rad) {
    if (!IsFinitePosition(position_rad)) {
        return false;
    }
    SoftLimitRange candidate = range_;
    candidate.upper_rad = position_rad;
    candidate.upper_valid = true;
    return CommitRange(candidate);
}

bool SoftLimitLearning::CaptureLowerFromObserved() {
    if (!has_observed_state_) {
        return false;
    }
    return CaptureLower(observed_state_.position_rad);
}

bool SoftLimitLearning::CaptureUpperFromObserved() {
    if (!has_observed_state_) {
        return false;
    }
    return CaptureUpper(observed_state_.position_rad);
}

bool SoftLimitLearning::SetRange(float lower_rad, float upper_rad) {
    if (!IsFinitePosition(lower_rad) || !IsFinitePosition(upper_rad)) {
        return false;
    }
    SoftLimitRange candidate{};
    candidate.lower_rad = lower_rad;
    candidate.upper_rad = upper_rad;
    candidate.lower_valid = true;
    candidate.upper_valid = true;
    return CommitRange(candidate);
}

bool SoftLimitLearning::SetRangeByLowerAndTravel(float lower_rad, float travel_rad) {
    if (!IsFinitePosition(lower_rad) || !scalar::is_finite_scalar(travel_rad) ||
        travel_rad < 0.0f) {
        return false;
    }
    const float margin = ClampNonNegative(kLearnedLimitMarginRad);
    if (travel_rad < 2.0f * margin) {
        return false;
    }
    return SetRange(lower_rad + margin, lower_rad + travel_rad - margin);
}

bool SoftLimitLearning::SetRangeByUpperAndTravel(float upper_rad, float travel_rad) {
    if (!IsFinitePosition(upper_rad) || !scalar::is_finite_scalar(travel_rad) ||
        travel_rad < 0.0f) {
        return false;
    }
    const float margin = ClampNonNegative(kLearnedLimitMarginRad);
    if (travel_rad < 2.0f * margin) {
        return false;
    }
    return SetRange(upper_rad - travel_rad + margin, upper_rad - margin);
}

bool SoftLimitLearning::HasObservedState() const {
    return has_observed_state_;
}

const MotorState& SoftLimitLearning::GetObservedState() const {
    return observed_state_;
}

bool SoftLimitLearning::HasLower() const {
    return range_.lower_valid;
}

bool SoftLimitLearning::HasUpper() const {
    return range_.upper_valid;
}

bool SoftLimitLearning::HasRange() const {
    return range_.lower_valid && range_.upper_valid;
}

bool SoftLimitLearning::IsSeeking() const {
    return state_ == SoftLimitLearningState::SeekingLower ||
           state_ == SoftLimitLearningState::SeekingUpper;
}

bool SoftLimitLearning::IsReady() const {
    return state_ == SoftLimitLearningState::Ready;
}

bool SoftLimitLearning::IsFailed() const {
    return state_ == SoftLimitLearningState::Failed;
}

float SoftLimitLearning::GetTravelRad() const {
    return HasRange() ? (range_.upper_rad - range_.lower_rad) : 0.0f;
}

float SoftLimitLearning::GetCenterRad() const {
    if (HasRange()) {
        return 0.5f * (range_.lower_rad + range_.upper_rad);
    }
    if (range_.lower_valid) {
        return range_.lower_rad;
    }
    if (range_.upper_valid) {
        return range_.upper_rad;
    }
    return has_observed_state_ ? observed_state_.position_rad : 0.0f;
}

float SoftLimitLearning::ClampPosition(float position_rad) const {
    return ClampPosition(position_rad, config_.limit_margin_rad);
}

float SoftLimitLearning::ClampPosition(float position_rad, float margin_rad) const {
    float value = IsFinitePosition(position_rad) ? position_rad : GetCenterRad();
    const float margin = ResolveMargin(margin_rad);

    if (range_.lower_valid && range_.upper_valid) {
        float lower = range_.lower_rad + margin;
        float upper = range_.upper_rad - margin;
        if (lower > upper) {
            const float center = 0.5f * (range_.lower_rad + range_.upper_rad);
            lower = center;
            upper = center;
        }
        const float in[1] = {value};
        float out[1] = {value};
        const auto limits = BuildRangeLimits(lower, upper);
        scalar::apply_range_limits(limits, in, out);
        return out[0];
    }

    if (range_.lower_valid && value < range_.lower_rad + margin) {
        value = range_.lower_rad + margin;
    }
    if (range_.upper_valid && value > range_.upper_rad - margin) {
        value = range_.upper_rad - margin;
    }
    return value;
}

float SoftLimitLearning::LimitVelocity(float position_rad,
                                       float velocity_rad_s) const {
    return LimitVelocity(position_rad, velocity_rad_s, config_.limit_margin_rad);
}

float SoftLimitLearning::LimitVelocity(float position_rad,
                                       float velocity_rad_s,
                                       float margin_rad) const {
    if (!IsFinitePosition(position_rad) ||
        !scalar::is_finite_scalar(velocity_rad_s)) {
        return 0.0f;
    }

    const float margin = ResolveMargin(margin_rad);
    if (range_.lower_valid &&
        position_rad <= range_.lower_rad + margin &&
        velocity_rad_s < 0.0f) {
        return 0.0f;
    }
    if (range_.upper_valid &&
        position_rad >= range_.upper_rad - margin &&
        velocity_rad_s > 0.0f) {
        return 0.0f;
    }
    return velocity_rad_s;
}

bool SoftLimitLearning::IsPositionWithinRange(float position_rad) const {
    return IsPositionWithinRange(position_rad, config_.limit_margin_rad);
}

bool SoftLimitLearning::IsPositionWithinRange(float position_rad,
                                              float margin_rad) const {
    if (!IsFinitePosition(position_rad)) {
        return false;
    }
    const float margin = ResolveMargin(margin_rad);
    if (range_.lower_valid && position_rad < range_.lower_rad + margin) {
        return false;
    }
    if (range_.upper_valid && position_rad > range_.upper_rad - margin) {
        return false;
    }
    return true;
}

bool SoftLimitLearning::IsAtLowerLimit(float position_rad) const {
    return IsAtLowerLimit(position_rad, config_.limit_margin_rad);
}

bool SoftLimitLearning::IsAtLowerLimit(float position_rad,
                                       float margin_rad) const {
    return range_.lower_valid && IsFinitePosition(position_rad) &&
           position_rad <= range_.lower_rad + ResolveMargin(margin_rad);
}

bool SoftLimitLearning::IsAtUpperLimit(float position_rad) const {
    return IsAtUpperLimit(position_rad, config_.limit_margin_rad);
}

bool SoftLimitLearning::IsAtUpperLimit(float position_rad,
                                       float margin_rad) const {
    return range_.upper_valid && IsFinitePosition(position_rad) &&
           position_rad >= range_.upper_rad - ResolveMargin(margin_rad);
}

const SoftLimitRange& SoftLimitLearning::GetRange() const {
    return range_;
}

bool SoftLimitLearning::GetLearnedLowerLimit(float& lower_rad) const {
    if (!range_.lower_valid) {
        return false;
    }
    lower_rad = range_.lower_rad;
    return true;
}

bool SoftLimitLearning::GetLearnedUpperLimit(float& upper_rad) const {
    if (!range_.upper_valid) {
        return false;
    }
    upper_rad = range_.upper_rad;
    return true;
}

bool SoftLimitLearning::GetLearnedLimits(float& lower_rad, float& upper_rad) const {
    if (!HasRange()) {
        return false;
    }
    lower_rad = range_.lower_rad;
    upper_rad = range_.upper_rad;
    return true;
}

SoftLimitLearningState SoftLimitLearning::GetState() const {
    return state_;
}

float SoftLimitLearning::GetSeekVelocity() const {
    return IsSeeking() ? seek_velocity_rad_s_ : 0.0f;
}

SoftLimitLearningWorkflow SoftLimitLearning::GetWorkflow() const {
    return workflow_;
}

void SoftLimitLearning::SetPostLearnReturnTarget(SoftLimitReturnTarget target) {
    post_learn_return_target_ = target;
    if (state_ == SoftLimitLearningState::Ready && target != SoftLimitReturnTarget::None) {
        post_learn_target_position_rad_ = GetPostLearnTargetPosition();
        post_learn_target_available_ = true;
    } else if (target == SoftLimitReturnTarget::None) {
        post_learn_target_available_ = false;
    }
}

SoftLimitReturnTarget SoftLimitLearning::GetPostLearnReturnTarget() const {
    return post_learn_return_target_;
}

bool SoftLimitLearning::HasPostLearnTargetPosition() const {
    return post_learn_target_available_;
}

float SoftLimitLearning::GetPostLearnTargetPosition() const {
    float target = GetCenterRad();
    switch (post_learn_return_target_) {
        case SoftLimitReturnTarget::Lower:
            target = range_.lower_valid ? range_.lower_rad : GetCenterRad();
            break;
        case SoftLimitReturnTarget::Upper:
            target = range_.upper_valid ? range_.upper_rad : GetCenterRad();
            break;
        case SoftLimitReturnTarget::Center:
            target = GetCenterRad();
            break;
        case SoftLimitReturnTarget::None:
        default:
            target = has_observed_state_ ? observed_state_.position_rad : GetCenterRad();
            break;
    }
    return ClampPosition(target);
}

float SoftLimitLearning::GetPendingTravelRad() const {
    return pending_travel_rad_;
}

uint16_t SoftLimitLearning::GetStallCycles() const {
    return stall_cycles_;
}

float SoftLimitLearning::GetElapsedSeekS() const {
    return elapsed_seek_s_;
}

float SoftLimitLearning::GetStartupIgnoreLeftS() const {
    return startup_ignore_left_s_;
}

bool SoftLimitLearning::CommitRange(SoftLimitRange range) {
    if (!NormalizeRangeCandidate(range, config_.min_range_rad)) {
        return false;
    }
    if (IsSeeking()) {
        ResetSeekTracking();
    }
    range_ = range;
    state_ = ResolveIdleState();
    if (state_ == SoftLimitLearningState::Ready &&
        post_learn_return_target_ != SoftLimitReturnTarget::None) {
        post_learn_target_position_rad_ = GetPostLearnTargetPosition();
        post_learn_target_available_ = true;
    } else {
        post_learn_target_available_ = false;
    }
    return true;
}

void SoftLimitLearning::FinishSeekAt(float position_rad) {
    const bool captured_upper = state_ == SoftLimitLearningState::SeekingUpper;
    if (workflow_ == SoftLimitLearningWorkflow::LowerWithTravel) {
        ResetSeekTracking();
        if (!CompleteSingleSideWithTravel(position_rad, false)) {
            ClearWorkflow();
            state_ = SoftLimitLearningState::Failed;
        }
        return;
    }
    if (workflow_ == SoftLimitLearningWorkflow::UpperWithTravel) {
        ResetSeekTracking();
        if (!CompleteSingleSideWithTravel(position_rad, true)) {
            ClearWorkflow();
            state_ = SoftLimitLearningState::Failed;
        }
        return;
    }
    if (workflow_ == SoftLimitLearningWorkflow::UpperThenLower ||
        workflow_ == SoftLimitLearningWorkflow::LowerThenUpper) {
        if (ContinueSequenceAfterFirstSide(captured_upper, position_rad)) {
            return;
        }
    }

    SoftLimitRange candidate = range_;
    if (state_ == SoftLimitLearningState::SeekingLower) {
        candidate.lower_rad = position_rad;
        candidate.lower_valid = true;
    } else if (state_ == SoftLimitLearningState::SeekingUpper) {
        candidate.upper_rad = position_rad;
        candidate.upper_valid = true;
    }

    ResetSeekTracking();
    if (!CommitRange(candidate)) {
        state_ = SoftLimitLearningState::Failed;
        ClearWorkflow();
    } else if (state_ == SoftLimitLearningState::Ready) {
        ClearWorkflow();
    }
}

void SoftLimitLearning::ResetSeekTracking() {
    seek_velocity_rad_s_ = 0.0f;
    last_seek_position_rad_ = 0.0f;
    seek_position_initialized_ = false;
    stall_cycles_ = 0u;
    elapsed_seek_s_ = 0.0f;
    startup_ignore_left_s_ = ClampNonNegative(kSeekStartupIgnoreS);
    ResetObserverTimer();
}

void SoftLimitLearning::ClearWorkflow() {
    workflow_ = SoftLimitLearningWorkflow::None;
    pending_travel_rad_ = 0.0f;
    pending_seek_speed_rad_s_ = 0.0f;
}

bool SoftLimitLearning::CompleteSingleSideWithTravel(float position_rad, bool upper_side) {
    const bool ok = upper_side ? SetRangeByUpperAndTravel(position_rad, pending_travel_rad_)
                               : SetRangeByLowerAndTravel(position_rad, pending_travel_rad_);
    ClearWorkflow();
    return ok;
}

bool SoftLimitLearning::ContinueSequenceAfterFirstSide(bool captured_upper,
                                                       float captured_position_rad) {
    if (workflow_ == SoftLimitLearningWorkflow::UpperThenLower) {
        if (captured_upper) {
            SoftLimitRange candidate = range_;
            candidate.upper_rad = captured_position_rad;
            candidate.upper_valid = true;
            if (!NormalizeRangeCandidate(candidate, config_.min_range_rad)) {
                ClearWorkflow();
                ResetSeekTracking();
                state_ = SoftLimitLearningState::Failed;
                return true;
            }
            range_ = candidate;
            ResetSeekTracking();
            seek_velocity_rad_s_ = -pending_seek_speed_rad_s_;
            state_ = SoftLimitLearningState::SeekingLower;
            return true;
        }
        ClearWorkflow();
        ResetSeekTracking();
        state_ = SoftLimitLearningState::Failed;
        return true;
    }

    if (workflow_ == SoftLimitLearningWorkflow::LowerThenUpper) {
        if (!captured_upper) {
            SoftLimitRange candidate = range_;
            candidate.lower_rad = captured_position_rad;
            candidate.lower_valid = true;
            if (!NormalizeRangeCandidate(candidate, config_.min_range_rad)) {
                ClearWorkflow();
                ResetSeekTracking();
                state_ = SoftLimitLearningState::Failed;
                return true;
            }
            range_ = candidate;
            ResetSeekTracking();
            seek_velocity_rad_s_ = pending_seek_speed_rad_s_;
            state_ = SoftLimitLearningState::SeekingUpper;
            return true;
        }
        ClearWorkflow();
        ResetSeekTracking();
        state_ = SoftLimitLearningState::Failed;
        return true;
    }

    return false;
}

SoftLimitLearningState SoftLimitLearning::ResolveIdleState() const {
    return HasRange() ? SoftLimitLearningState::Ready : SoftLimitLearningState::Idle;
}

float SoftLimitLearning::ResolveMargin(float margin_rad) const {
    return ClampFiniteNonNegative(margin_rad, config_.limit_margin_rad);
}

} // namespace mr::motor
