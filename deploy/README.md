# MRobot static origin

The production origin is a static Caddy service. Update discovery uses
`https://updates.qutmrobot.cn`; versioned installers and the cloud part library
use `https://download.qutmrobot.cn`. It contains no application runtime or
database.

```text
/srv/mrobot/
├── stable/
│   └── update.json
├── releases/
│   └── vX.Y.Z/
│       ├── MRobot-vX.Y.Z-macos-arm64.dmg
│       ├── MRobot-vX.Y.Z-windows-x64-setup.exe
│       └── MRobot-vX.Y.Z-linux-x64.tar.gz
└── parts/
    └── v1/
        ├── catalog.json
        └── files/
            └── 机械/...
```

Versioned artifacts are uploaded before the stable manifest is replaced. Caddy
serves release files with a long immutable cache policy, part files with a
seven-day immutable cache policy, and prevents caching of update and part
catalogue manifests. GitHub Releases remains the fallback update source.

Build a part-library deployment tree with:

```bash
python tools/build_part_catalog.py \
  --source /path/to/零件库.zip \
  --output part-dist/v1
```

The builder publishes only the `机械` collection, removes SolidWorks lock
files, repairs legacy Chinese ZIP names, and writes `catalog.json`. Upload a new
tree to `/srv/mrobot/parts/v1-next`, verify the manifest file count, every
declared path, and the summed byte size on the server, then atomically promote
it to `/srv/mrobot/parts/v1`. Never modify a live tree in place. File URLs carry
the manifest version as a query parameter, so a new catalogue bypasses cached
older content.

The server accepts release uploads through the unprivileged `mrobotdeploy`
account. Administrative SSH credentials and code-signing keys must never be
stored on the server or committed to this repository.

DNS must contain this record before Caddy can obtain the TLS certificate:

```text
updates  A  43.161.216.136
download A  43.161.216.136
```
