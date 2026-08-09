# MRobot update origin

The production update origin is a static Caddy service. Update discovery uses
`https://updates.qutmrobot.cn`, while versioned installers use
`https://download.qutmrobot.cn`. It contains no application runtime or database.

```text
/srv/mrobot/
├── stable/
│   └── update.json
└── releases/
    └── vX.Y.Z/
        ├── MRobot-vX.Y.Z-macos-arm64.dmg
        ├── MRobot-vX.Y.Z-windows-x64-setup.exe
        └── MRobot-vX.Y.Z-linux-x64.tar.gz
```

Versioned artifacts are uploaded before the stable manifest is replaced. Caddy
serves versioned files with an immutable cache policy and prevents caching of
the stable manifest. GitHub Releases remains the fallback update source.

The server accepts release uploads through the unprivileged `mrobotdeploy`
account. Administrative SSH credentials and code-signing keys must never be
stored on the server or committed to this repository.

DNS must contain this record before Caddy can obtain the TLS certificate:

```text
updates  A  43.161.216.136
download A  43.161.216.136
```
