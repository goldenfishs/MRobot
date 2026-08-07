# MCode

MCode is the headless STM32CubeMX project analysis, package resolution, generation and validation engine for the [MRobot](https://github.com/goldenfishs/MRobot) ecosystem.

Every front end calls the same API:

```python
from mcode import MCodeService

service = MCodeService()
model = service.inspect("/path/to/cubemx-project")
plan = service.plan("/path/to/cubemx-project")
```

The CLI exposes the same operations with stable JSON output:

```bash
mcode inspect . --json
mcode init .
mcode plan .
mcode generate .
mcode validate . --json
mcode package validate /path/to/package
```

MCode currently supports STM32CubeMX first. MCU families outside STM32 will be added through separate platform packs after the package and lockfile protocols stabilize.
