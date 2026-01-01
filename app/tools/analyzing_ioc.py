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