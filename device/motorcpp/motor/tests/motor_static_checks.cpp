#include "device/motor/core/motor_t.hpp"
#include "device/motor/core/motor_aliases.hpp"

namespace mr::motor::tests {

using RmM2006 = MotorT<MotorKind::RM, MotorModel::M2006>;
using RmM3508 = MotorT<MotorKind::RM, MotorModel::M3508>;
using RmM6020 = MotorT<MotorKind::RM, MotorModel::M6020>;
using DmJ10010 = MotorT<MotorKind::DM, MotorModel::J10010>;
using DmJ10422P = MotorT<MotorKind::DM, MotorModel::J10422P>;
using DmJ3507 = MotorT<MotorKind::DM, MotorModel::J3507>;
using DmJ4310 = MotorT<MotorKind::DM, MotorModel::J4310>;
using DmJ4310P = MotorT<MotorKind::DM, MotorModel::J4310P>;
using DmJ4340 = MotorT<MotorKind::DM, MotorModel::J4340>;
using DmJ6248P = MotorT<MotorKind::DM, MotorModel::J6248P>;
using DmJ8009P = MotorT<MotorKind::DM, MotorModel::J8009P>;
using LzRso0 = MotorT<MotorKind::LZ, MotorModel::RSO0>;
using LzRso1 = MotorT<MotorKind::LZ, MotorModel::RSO1>;
using LzRso2 = MotorT<MotorKind::LZ, MotorModel::RSO2>;
using LzRso3 = MotorT<MotorKind::LZ, MotorModel::RSO3>;
using LzRso4 = MotorT<MotorKind::LZ, MotorModel::RSO4>;
using LzRso5 = MotorT<MotorKind::LZ, MotorModel::RSO5>;
using LzRso6 = MotorT<MotorKind::LZ, MotorModel::RSO6>;

static_assert(MotorModelValidV<MotorKind::RM, MotorModel::M2006>, "RM + M2006 should be valid");
static_assert(MotorModelValidV<MotorKind::RM, MotorModel::M3508>, "RM + M3508 should be valid");
static_assert(MotorModelValidV<MotorKind::RM, MotorModel::M6020>, "RM + M6020 should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J10010>, "DM + J10010 should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J10422P>, "DM + J10422P should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J3507>, "DM + J3507 should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J4310>, "DM + J4310 should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J4310P>, "DM + J4310P should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J4340>, "DM + J4340 should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J6248P>, "DM + J6248P should be valid");
static_assert(MotorModelValidV<MotorKind::DM, MotorModel::J8009P>, "DM + J8009P should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO0>, "LZ + RSO0 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO1>, "LZ + RSO1 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO2>, "LZ + RSO2 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO3>, "LZ + RSO3 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO4>, "LZ + RSO4 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO5>, "LZ + RSO5 should be valid");
static_assert(MotorModelValidV<MotorKind::LZ, MotorModel::RSO6>, "LZ + RSO6 should be valid");

static_assert(!MotorModelValidV<MotorKind::RM, MotorModel::J4310>, "RM + J4310 must be invalid");
static_assert(!MotorModelValidV<MotorKind::DM, MotorModel::M3508>, "DM + M3508 must be invalid");
static_assert(!MotorModelValidV<MotorKind::LZ, MotorModel::M6020>, "LZ + M6020 must be invalid");

static_assert(RmM2006::Traits::kSupportsTorque, "RM M2006 should support torque");
static_assert(!RmM2006::Traits::kSupportsMit, "RM M2006 should not support MIT");
static_assert(!RmM2006::Traits::kSupportsPosition, "RM M2006 should not advertise unsupported position API");
static_assert(DmJ4310::Traits::kSupportsMit, "DM J4310 should support MIT");
static_assert(DmJ4310P::Traits::kSupportsMit, "DM J4310P should support MIT");
static_assert(DmJ4340::Traits::kSupportsMit, "DM J4340 should support MIT");
static_assert(DmJ10422P::Traits::kSupportsMit, "DM J10422P should support MIT");
static_assert(LzRso0::Traits::kSupportsPosition, "LZ RSO0 should support position");
static_assert(LzRso3::Traits::kSupportsPosition, "LZ RSO3 should support position");
static_assert(LzRso6::Traits::kSupportsMit, "LZ RSO6 should support MIT");

static_assert(RmM3508::Traits::kKind == MotorKind::RM, "Traits kind mismatch");
static_assert(DmJ4310::Traits::kModel == MotorModel::J4310, "Traits model mismatch");
static_assert(DmJ4310P::Traits::kModel == MotorModel::J4310P, "Traits model mismatch");
static_assert(DmJ4340::Traits::kModel == MotorModel::J4340, "Traits model mismatch");
static_assert(DmJ6248P::Traits::kModel == MotorModel::J6248P, "Traits model mismatch");
static_assert(LzRso3::Traits::kHasHostId, "LZ should expose host id capability");

static_assert(RmM2006::capabilities() == RmM2006::Traits::kCapabilities, "RM2006 capabilities mismatch");
static_assert(RmM3508::capabilities() == RmM3508::Traits::kCapabilities, "RM3508 capabilities mismatch");
static_assert(RmM6020::capabilities() == RmM6020::Traits::kCapabilities, "RM6020 capabilities mismatch");
static_assert(DmJ4310::capabilities() == DmJ4310::Traits::kCapabilities, "DMJ4310 capabilities mismatch");
static_assert(DmJ4310P::capabilities() == DmJ4310P::Traits::kCapabilities, "DMJ4310P capabilities mismatch");
static_assert(DmJ4340::capabilities() == DmJ4340::Traits::kCapabilities, "DMJ4340 capabilities mismatch");
static_assert(DmJ8009P::capabilities() == DmJ8009P::Traits::kCapabilities, "DMJ8009P capabilities mismatch");

static_assert(RmM2006::peak_current() == RmM2006::Traits::kPeakCurrent, "RM2006 peak current mismatch");
static_assert(RmM3508::peak_current() == RmM3508::Traits::kPeakCurrent, "RM3508 peak current mismatch");
static_assert(DmJ4310::peak_torque() == DmJ4310::Traits::kPeakTorque, "DMJ4310 peak torque mismatch");
static_assert(DmJ4310P::peak_torque() == DmJ4310P::Traits::kPeakTorque, "DMJ4310P peak torque mismatch");
static_assert(DmJ4340::peak_torque() == DmJ4340::Traits::kPeakTorque, "DMJ4340 peak torque mismatch");
static_assert(DmJ10010::peak_torque() == DmJ10010::Traits::kPeakTorque, "DMJ10010 peak torque mismatch");
static_assert(LzRso0::peak_torque() == LzRso0::Traits::kPeakTorque, "LZ RSO0 peak torque mismatch");
static_assert(LzRso3::peak_torque() == LzRso3::Traits::kPeakTorque, "LZ peak torque mismatch");
static_assert(LzRso6::peak_torque() == LzRso6::Traits::kPeakTorque, "LZ RSO6 peak torque mismatch");

static_assert(DmJ10422P::Traits::kReducerRatio == 22.0f, "DMJ10422P reducer ratio mismatch");
static_assert(DmJ3507::Traits::kEncoderCpr == 16383, "DMJ3507 encoder resolution mismatch");
static_assert(DmJ6248P::Traits::kRatedSupplyCurrent == 7.0f, "DMJ6248P supply current mismatch");
static_assert(LzRso0::Traits::kPeakTorque == 14.0f, "RS00 peak torque from manual");
static_assert(LzRso1::Traits::kRatedVoltage == 36.0f, "RS01 rated voltage from manual");
static_assert(LzRso2::Traits::kPeakTorque == 17.0f, "RS02 peak torque from manual");
static_assert(LzRso3::Traits::kReducerRatio == 9.0f, "RS03 reducer ratio from manual");
static_assert(LzRso4::Traits::kPeakTorque == 120.0f, "RS04 peak torque from manual");
static_assert(LzRso5::Traits::kRatedTorque == 1.6f, "RS05 rated torque from manual");
static_assert(LzRso6::Traits::kPeakCurrent == 57.0f, "RS06 peak current from manual");

static_assert(RmM2006::kind() == MotorKind::RM, "RM2006 vendor mismatch");
static_assert(DmJ4310::kind() == MotorKind::DM, "DMJ4310 vendor mismatch");
static_assert(DmJ4310P::kind() == MotorKind::DM, "DMJ4310P vendor mismatch");
static_assert(DmJ4340::kind() == MotorKind::DM, "DMJ4340 vendor mismatch");
static_assert(LzRso3::kind() == MotorKind::LZ, "LZRSO3 vendor mismatch");
static_assert(LzRso3::model() == MotorModel::RSO3, "LZRSO3 model mismatch");

static_assert(std::is_same_v<RmM3508Motor, RmM3508>, "RM alias mismatch");
static_assert(std::is_same_v<DmJ10010Motor, DmJ10010>, "DM alias mismatch");
static_assert(std::is_same_v<DmJ4310Motor, DmJ4310>, "DM alias mismatch");
static_assert(std::is_same_v<DmJ4310PMotor, DmJ4310P>, "DM alias mismatch");
static_assert(std::is_same_v<DmJ4340Motor, DmJ4340>, "DM alias mismatch");
static_assert(std::is_same_v<DmJ6248PMotor, DmJ6248P>, "DM alias mismatch");
static_assert(std::is_same_v<LzRso0Motor, LzRso0>, "LZ alias mismatch");
static_assert(std::is_same_v<LzRso3Motor, LzRso3>, "LZ alias mismatch");
static_assert(std::is_same_v<LzRso6Motor, LzRso6>, "LZ alias mismatch");

} // namespace mr::motor::tests