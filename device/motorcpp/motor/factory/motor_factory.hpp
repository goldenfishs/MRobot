#pragma once

// 强类型电机对象静态工厂。
// 负责在固定静态存储区内构造不同 kind/model 的 MotorT 实例，避免动态堆分配。

#include <new>
#include <stdint.h>

#include "device/motor/core/motor_install_spec.hpp"
#include "device/motor/core/motor_t.hpp"

namespace mr::motor {

inline constexpr uint8_t kRmMotorFactoryCapacity = 16;
inline constexpr uint8_t kDmMotorFactoryCapacity = 8;
inline constexpr uint8_t kLzMotorFactoryCapacity = 8;

class MotorFactory {
public:
    template <MotorKind Kind, MotorModel Model>
    static MotorT<Kind, Model>* Create(
        const MotorInstanceConfig<Kind>&  config,
        const MotorInstallSpec& install = kDirectDriveInstall,
        const MotorTemperatureProtectionConfig& temperature_protection = {}) {
        static_assert(MotorModelValidV<Kind, Model>, "Invalid motor kind/model combination");
        using MotorType = MotorT<Kind, Model>;
        static DriverSlot<MotorType> drivers[Capacity<Kind>()];
        uint8_t& count = Counter<Kind>();
        if (count >= Capacity<Kind>()) {
            return nullptr;
        }
        MotorType* driver =
            new (&drivers[count].value) MotorType(config, install, temperature_protection);
        ++count;
        return driver;
    }

private:
    template <typename T>
    union DriverSlot {
        DriverSlot() {}
        ~DriverSlot() {}
        T value;
    };

    template <MotorKind Kind>
    static constexpr uint8_t Capacity();

    template <MotorKind Kind>
    static uint8_t& Counter();

    static uint8_t rm_count_;
    static uint8_t dm_count_;
    static uint8_t lz_count_;
};

template <>
inline constexpr uint8_t MotorFactory::Capacity<MotorKind::RM>() { return kRmMotorFactoryCapacity; }

template <>
inline constexpr uint8_t MotorFactory::Capacity<MotorKind::DM>() { return kDmMotorFactoryCapacity; }

template <>
inline constexpr uint8_t MotorFactory::Capacity<MotorKind::LZ>() { return kLzMotorFactoryCapacity; }

template <>
inline uint8_t& MotorFactory::Counter<MotorKind::RM>() { return rm_count_; }

template <>
inline uint8_t& MotorFactory::Counter<MotorKind::DM>() { return dm_count_; }

template <>
inline uint8_t& MotorFactory::Counter<MotorKind::LZ>() { return lz_count_; }

} // namespace mr::motor
