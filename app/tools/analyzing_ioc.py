class analyzing_ioc:
    @staticmethod
    def is_freertos_enabled_from_ioc(ioc_path):
        """
        检查指定 .ioc 文件是否开启了 FreeRTOS
        """
        config = {}
        with open(ioc_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        ip_keys = [k for k in config if k.startswith('Mcu.IP')]
        for k in ip_keys:
            if config[k] == 'FREERTOS':
                return True
        for k in config:
            if k.startswith('FREERTOS.'):
                return True
        return False

    @staticmethod
    def get_enabled_i2c_from_ioc(ioc_path):
        """
        从.ioc文件中获取已启用的I2C列表
        返回格式: ['I2C1', 'I2C3'] 等
        """
        enabled_i2c = []
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 检查是否启用了I2C
                    if key.startswith('Mcu.IP') and value.startswith('I2C'):
                        # 提取I2C编号，如I2C1, I2C2等
                        i2c_name = value.split('.')[0] if '.' in value else value
                        if i2c_name not in enabled_i2c:
                            enabled_i2c.append(i2c_name)
        return sorted(enabled_i2c)
    
    @staticmethod
    def get_enabled_spi_from_ioc(ioc_path):
        """
        获取已启用的SPI列表
        返回格式: ['SPI1', 'SPI2'] 等
        """
        enabled_spi = []
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key.startswith('Mcu.IP') and value.startswith('SPI'):
                        spi_name = value.split('.')[0] if '.' in value else value
                        if spi_name not in enabled_spi:
                            enabled_spi.append(spi_name)
        return sorted(enabled_spi)

    @staticmethod
    def get_enabled_can_from_ioc(ioc_path):
        """
        获取已启用的CAN列表（不包括FDCAN）
        返回格式: ['CAN1', 'CAN2'] 等
        """
        enabled_can = []
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 只匹配CAN，不包括FDCAN
                    if key.startswith('Mcu.IP') and value.startswith('CAN') and not value.startswith('FDCAN'):
                        can_name = value.split('.')[0] if '.' in value else value
                        if can_name not in enabled_can:
                            enabled_can.append(can_name)
        return sorted(enabled_can)

    @staticmethod
    def get_enabled_fdcan_from_ioc(ioc_path):
        """
        获取已启用的FDCAN列表
        返回格式: ['FDCAN1', 'FDCAN2', 'FDCAN3'] 等
        """
        enabled_fdcan = []
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key.startswith('Mcu.IP') and value.startswith('FDCAN'):
                        fdcan_name = value.split('.')[0] if '.' in value else value
                        if fdcan_name not in enabled_fdcan:
                            enabled_fdcan.append(fdcan_name)
        return sorted(enabled_fdcan)

    @staticmethod
    def get_enabled_uart_from_ioc(ioc_path):
        """
        获取已启用的UART/USART列表
        返回格式: ['USART1', 'USART2', 'UART4'] 等
        """
        enabled_uart = []
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 检查是否启用了UART或USART
                    if key.startswith('Mcu.IP') and (value.startswith('USART') or value.startswith('UART')):
                        uart_name = value.split('.')[0] if '.' in value else value
                        if uart_name not in enabled_uart:
                            enabled_uart.append(uart_name)
        return sorted(enabled_uart)
    

    @staticmethod
    def get_enabled_gpio_from_ioc(ioc_path):
        """
        获取所有带 EXTI 且有 Label 的 GPIO，排除其他外设功能的引脚
        """
        gpio_list = []
        gpio_configs = {}
        
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 收集GPIO相关配置
                    if '.' in key:
                        pin = key.split('.')[0]
                        param = key.split('.', 1)[1]
                        
                        if pin not in gpio_configs:
                            gpio_configs[pin] = {}
                        
                        gpio_configs[pin][param] = value
        
        # 定义需要排除的Signal类型
        excluded_signals = [
            'SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'SPI2_SCK', 'SPI2_MISO', 'SPI2_MOSI', 
            'SPI3_SCK', 'SPI3_MISO', 'SPI3_MOSI',
            'I2C1_SCL', 'I2C1_SDA', 'I2C2_SCL', 'I2C2_SDA', 'I2C3_SCL', 'I2C3_SDA',
            'USART1_TX', 'USART1_RX', 'USART2_TX', 'USART2_RX', 'USART3_TX', 'USART3_RX',
            'USART6_TX', 'USART6_RX', 'UART4_TX', 'UART4_RX', 'UART5_TX', 'UART5_RX',
            'CAN1_TX', 'CAN1_RX', 'CAN2_TX', 'CAN2_RX',
            'USB_OTG_FS_DM', 'USB_OTG_FS_DP', 'USB_OTG_HS_DM', 'USB_OTG_HS_DP',
            'SYS_JTMS-SWDIO', 'SYS_JTCK-SWCLK', 'SYS_JTDI', 'SYS_JTDO-SWO',
            'RCC_OSC_IN', 'RCC_OSC_OUT',
        ]
        
        # 处理每个GPIO配置，只选择EXTI类型的
        for pin, config in gpio_configs.items():
            signal = config.get('Signal', '')
            
            # 只处理有Label和EXTI功能的GPIO
            if ('GPIO_Label' not in config or 
                ('GPIO_ModeDefaultEXTI' not in config and not signal.startswith('GPXTI'))):
                continue
                
            # 排除用于其他外设功能的引脚
            if signal in excluded_signals or signal.startswith('S_TIM') or signal.startswith('ADC'):
                continue
                
            # 只包含EXTI功能的GPIO
            if signal.startswith('GPXTI'):
                label = config['GPIO_Label']
                gpio_list.append({'pin': pin, 'label': label})
        
        return gpio_list



    @staticmethod  
    def get_all_gpio_from_ioc(ioc_path):
        """
        获取所有GPIO配置，但排除用于其他外设功能的引脚
        只包含纯GPIO功能：GPIO_Input, GPIO_Output, GPXTI
        """
        gpio_list = []
        gpio_configs = {}
        
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 收集GPIO相关配置
                    if '.' in key:
                        pin = key.split('.')[0]
                        param = key.split('.', 1)[1]
                        
                        if pin not in gpio_configs:
                            gpio_configs[pin] = {}
                        
                        gpio_configs[pin][param] = value
        
        # 定义需要排除的Signal类型（用于其他外设功能的）
        excluded_signals = [
            # SPI相关
            'SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'SPI2_SCK', 'SPI2_MISO', 'SPI2_MOSI', 
            'SPI3_SCK', 'SPI3_MISO', 'SPI3_MOSI',
            # I2C相关
            'I2C1_SCL', 'I2C1_SDA', 'I2C2_SCL', 'I2C2_SDA', 'I2C3_SCL', 'I2C3_SDA',
            # UART/USART相关
            'USART1_TX', 'USART1_RX', 'USART2_TX', 'USART2_RX', 'USART3_TX', 'USART3_RX',
            'USART6_TX', 'USART6_RX', 'UART4_TX', 'UART4_RX', 'UART5_TX', 'UART5_RX',
            # CAN相关
            'CAN1_TX', 'CAN1_RX', 'CAN2_TX', 'CAN2_RX',
            # USB相关
            'USB_OTG_FS_DM', 'USB_OTG_FS_DP', 'USB_OTG_HS_DM', 'USB_OTG_HS_DP',
            # 系统相关
            'SYS_JTMS-SWDIO', 'SYS_JTCK-SWCLK', 'SYS_JTDI', 'SYS_JTDO-SWO',
            'RCC_OSC_IN', 'RCC_OSC_OUT',
        ]
        
        # 处理每个GPIO配置
        for pin, config in gpio_configs.items():
            signal = config.get('Signal', '')
            
            # 只处理有Label的GPIO
            if 'GPIO_Label' not in config:
                continue
                
            # 排除用于其他外设功能的引脚
            if signal in excluded_signals:
                continue
                
            # 排除TIM相关的引脚（以S_TIM开头的信号）
            if signal.startswith('S_TIM'):
                continue
                
            # 排除ADC相关的引脚
            if signal.startswith('ADC'):
                continue
                
            # 只包含纯GPIO功能
            if signal in ['GPIO_Input', 'GPIO_Output'] or signal.startswith('GPXTI'):
                gpio_info = {
                    'pin': pin,
                    'label': config['GPIO_Label'],
                    'has_exti': 'GPIO_ModeDefaultEXTI' in config or signal.startswith('GPXTI'),
                    'signal': signal,
                    'mode': config.get('GPIO_ModeDefaultEXTI', ''),
                    'is_output': signal == 'GPIO_Output',
                    'is_input': signal == 'GPIO_Input'
                }
                gpio_list.append(gpio_info)
        
        return gpio_list
    
    @staticmethod
    def get_enabled_pwm_from_ioc(ioc_path):
        """
        获取已启用的PWM通道列表
        返回格式: [{'timer': 'TIM1', 'channel': 'TIM_CHANNEL_1', 'label': 'PWM_MOTOR1'}, ...]
        """
        pwm_channels = []
        gpio_configs = {}
        
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 收集GPIO相关配置
                    if '.' in key:
                        pin = key.split('.')[0]
                        param = key.split('.', 1)[1]
                        
                        if pin not in gpio_configs:
                            gpio_configs[pin] = {}
                        
                        gpio_configs[pin][param] = value
        
        # 处理每个GPIO配置，查找PWM信号
        for pin, config in gpio_configs.items():
            signal = config.get('Signal', '')
            
            # 检查是否为PWM信号（格式如：S_TIM1_CH1, S_TIM2_CH3等）
            if signal.startswith('S_TIM') and '_CH' in signal:
                # 解析定时器和通道信息
                # 例如：S_TIM1_CH1 -> TIM1, CH1
                parts = signal.replace('S_', '').split('_')
                if len(parts) >= 2:
                    timer = parts[0]  # TIM1
                    channel_part = parts[1]  # CH1
                    
                    # 转换通道格式：CH1 -> TIM_CHANNEL_1
                    if channel_part.startswith('CH'):
                        channel_num = channel_part[2:]  # 提取数字
                        channel = f"TIM_CHANNEL_{channel_num}"
                        
                        # 获取标签
                        label = config.get('GPIO_Label', f"{timer}_{channel_part}")
                        
                        pwm_channels.append({
                            'timer': timer,
                            'channel': channel,
                            'label': label,
                            'pin': pin,
                            'signal': signal
                        })
        
        return pwm_channels
    
    @staticmethod
    def get_mcu_name_from_ioc(ioc_path):
        """
        从.ioc文件中获取MCU型号
        返回格式: 'STM32F407IGHx' 等
        """
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 查找MCU名称
                    if key == 'Mcu.UserName' or key == 'Mcu.Name':
                        return value
        return None
    
    @staticmethod
    def get_flash_config_from_mcu(mcu_name):
        """
        根据MCU型号返回Flash配置
        支持STM32F1/F4/H7系列
        返回格式: {
            'sectors': [...],  # Sector/Page配置列表
            'dual_bank': False,  # 是否双Bank
            'end_address': 0x08100000,  # Flash结束地址
            'type': 'sector' or 'page'  # Flash类型
        }
        """
        if not mcu_name:
            return None
        
        mcu_upper = mcu_name.upper()
        
        # STM32F1系列 - 使用Page而不是Sector
        if mcu_upper.startswith('STM32F1'):
            return analyzing_ioc._get_stm32f1_flash_config(mcu_upper)
        
        # STM32F4系列 - 使用Sector
        elif mcu_upper.startswith('STM32F4'):
            return analyzing_ioc._get_stm32f4_flash_config(mcu_upper)
        
        # STM32H7系列 - 使用Sector
        elif mcu_upper.startswith('STM32H7'):
            return analyzing_ioc._get_stm32h7_flash_config(mcu_upper)
        
        return None
    
    @staticmethod
    def _get_stm32f1_flash_config(mcu_upper):
        """
        STM32F1系列Flash配置
        F1使用Page而不是Sector
        - 小/中容量设备: 1KB/page
        - 大容量/互联型设备: 2KB/page
        容量代码: 4/6=16/32KB, 8/B=64/128KB, C=256KB, D/E=384/512KB, F/G=768KB/1MB
        """
        flash_size_map_f1 = {
            '4': 16,    # 16KB
            '6': 32,    # 32KB
            '8': 64,    # 64KB
            'B': 128,   # 128KB
            'C': 256,   # 256KB
            'D': 384,   # 384KB
            'E': 512,   # 512KB
            'F': 768,   # 768KB (互联型)
            'G': 1024,  # 1MB (互联型)
        }
        
        # F1命名: STM32F103C8T6, C在索引9
        if len(mcu_upper) < 10:
            return None
        
        flash_code = mcu_upper[9]
        flash_size = flash_size_map_f1.get(flash_code)
        
        if not flash_size:
            return None
        
        # 判断页大小: <=128KB用1KB页, >128KB用2KB页
        page_size = 1 if flash_size <= 128 else 2
        num_pages = flash_size // page_size
        
        config = {
            'type': 'page',
            'dual_bank': False,
            'sectors': [],  # F1中这里存的是Page
            'page_size': page_size,
        }
        
        # 生成所有页
        current_address = 0x08000000
        for page_id in range(num_pages):
            config['sectors'].append({
                'id': page_id,
                'address': current_address,
                'size': page_size
            })
            current_address += page_size * 1024
        
        config['end_address'] = current_address
        return config
    
    @staticmethod
    def _get_stm32f4_flash_config(mcu_upper):
        """
        STM32F4系列Flash配置
        容量代码: C=256KB, E=512KB, G=1MB, I=2MB
        """
        flash_size_map = {
            'C': 256,   # 256KB
            'E': 512,   # 512KB
            'G': 1024,  # 1MB
            'I': 2048,  # 2MB
        }
        
        # F4命名: STM32F407IGHx, I在索引9
        if len(mcu_upper) < 10:
            return None
        
        flash_code = mcu_upper[9]
        flash_size = flash_size_map.get(flash_code)
        
        if not flash_size:
            return None
        
        config = {
            'type': 'sector',
            'dual_bank': False,
            'sectors': [],
        }
        
        # STM32F4系列单Bank Flash布局
        # Sector 0-3: 16KB each
        # Sector 4: 64KB
        # Sector 5-11: 128KB each (如果有)
        
        base_sectors = [
            {'id': 0, 'address': 0x08000000, 'size': 16},
            {'id': 1, 'address': 0x08004000, 'size': 16},
            {'id': 2, 'address': 0x08008000, 'size': 16},
            {'id': 3, 'address': 0x0800C000, 'size': 16},
            {'id': 4, 'address': 0x08010000, 'size': 64},
        ]
        
        config['sectors'] = base_sectors.copy()
        current_address = 0x08020000
        current_id = 5
        remaining_kb = flash_size - (16 * 4 + 64)  # 减去前5个sector
        
        # 添加128KB的sectors
        while remaining_kb > 0 and current_id < 12:
            config['sectors'].append({
                'id': current_id,
                'address': current_address,
                'size': 128
            })
            current_address += 0x20000  # 128KB
            remaining_kb -= 128
            current_id += 1
        
        # 设置结束地址
        config['end_address'] = current_address
        
        # 2MB Flash需要双Bank (Sector 12-23)
        if flash_size >= 2048:
            config['dual_bank'] = True
            # Bank 2 的sectors (12-15: 16KB, 16: 64KB, 17-23: 128KB)
            bank2_sectors = [
                {'id': 12, 'address': 0x08100000, 'size': 16},
                {'id': 13, 'address': 0x08104000, 'size': 16},
                {'id': 14, 'address': 0x08108000, 'size': 16},
                {'id': 15, 'address': 0x0810C000, 'size': 16},
                {'id': 16, 'address': 0x08110000, 'size': 64},
                {'id': 17, 'address': 0x08120000, 'size': 128},
                {'id': 18, 'address': 0x08140000, 'size': 128},
                {'id': 19, 'address': 0x08160000, 'size': 128},
                {'id': 20, 'address': 0x08180000, 'size': 128},
                {'id': 21, 'address': 0x081A0000, 'size': 128},
                {'id': 22, 'address': 0x081C0000, 'size': 128},
                {'id': 23, 'address': 0x081E0000, 'size': 128},
            ]
            config['sectors'].extend(bank2_sectors)
            config['end_address'] = 0x08200000
        
        return config
    
    @staticmethod
    def _get_stm32h7_flash_config(mcu_upper):
        """
        STM32H7系列Flash配置
        - 每个Sector 128KB
        - 单Bank: 8个Sector (1MB)
        - 双Bank: 16个Sector (2MB), 每个Bank 8个Sector
        容量代码: B=128KB, G=1MB, I=2MB
        命名格式: STM32H7 + 23 + V(引脚) + G(容量) + T(封装) + 6
        """
        flash_size_map_h7 = {
            'B': 128,   # 128KB (1个Sector)
            'G': 1024,  # 1MB (8个Sector, 单Bank)
            'I': 2048,  # 2MB (16个Sector, 双Bank)
        }
        
        # H7命名: STM32H723VGT6, G在索引10
        if len(mcu_upper) < 11:
            return None
        
        flash_code = mcu_upper[10]
        flash_size = flash_size_map_h7.get(flash_code)
        
        if not flash_size:
            return None
        
        config = {
            'type': 'sector',
            'dual_bank': flash_size >= 2048,
            'sectors': [],
        }
        
        num_sectors = flash_size // 128  # 每个Sector 128KB
        
        # 生成Sector配置
        current_address = 0x08000000
        for sector_id in range(num_sectors):
            config['sectors'].append({
                'id': sector_id,
                'address': current_address,
                'size': 128,
                'bank': 1 if sector_id < 8 else 2  # Bank信息
            })
            current_address += 0x20000  # 128KB
        
        config['end_address'] = current_address
        return config