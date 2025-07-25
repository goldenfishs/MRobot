class IocConfig:
    def __init__(self, ioc_path):
        self.ioc_path = ioc_path
        self.config = {}
        self._parse()

    def _parse(self):
        with open(self.ioc_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self.config[key.strip()] = value.strip()

    def is_freertos_enabled(self):
        ip_keys = [k for k in self.config if k.startswith('Mcu.IP')]
        for k in ip_keys:
            if self.config[k] == 'FREERTOS':
                return True
        for k in self.config:
            if k.startswith('FREERTOS.'):
                return True
        return False