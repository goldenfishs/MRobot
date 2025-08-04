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
        获取已启用的CAN列表
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
                    if key.startswith('Mcu.IP') and value.startswith('CAN'):
                        can_name = value.split('.')[0] if '.' in value else value
                        if can_name not in enabled_can:
                            enabled_can.append(can_name)
        return sorted(enabled_can)

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
        获取所有带 EXTI 且有 Label 的 GPIO，返回 [{'pin': 'PC4', 'label': 'ACCL_INT'}, ...]
        """
        gpio_list = []
        gpio_params = {}
        with open(ioc_path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if '.GPIOParameters' in key:
                        gpio_params[key.split('.')[0]] = value
                    elif '.GPIO_Label' in key:
                        pin = key.split('.')[0]
                        gpio_params[f"{pin}_label"] = value
                    elif '.GPIO_ModeDefaultEXTI' in key:
                        pin = key.split('.')[0]
                        gpio_params[f"{pin}_exti"] = value
        for pin in gpio_params:
            if not pin.endswith('_label') and not pin.endswith('_exti'):
                label = gpio_params.get(f"{pin}_label", None)
                exti = gpio_params.get(f"{pin}_exti", None)
                if label and exti:
                    gpio_list.append({'pin': pin, 'label': label})
        return gpio_list