# NABEEL outbound distribution

`scripts/nabeel-distribution.py` is the fail-closed outbound adapter for approved live destinations.

- destination configuration contains only secret **references** (`secret_env`), never stream keys;
- every destination has an explicit `enabled` flag;
- `status` reports readiness without revealing credentials;
- `run --dry-run` proves command construction with secrets redacted;
- an enabled destination with a missing secret exits non-zero and does not invoke FFmpeg.

Example:

```bash
scripts/nabeel-distribution.py --config docs/nabeel-destinations.example.json status
scripts/nabeel-distribution.py --config /secure/path/destinations.json run youtube --dry-run
```

Production/live publishing remains a separate explicit operation. A real private/unlisted destination test requires the corresponding credential to be supplied outside Git.

## Canonical Owncast destination

The canonical Owncast runtime remains on `codestra-desktop`. MediaMTX/FFmpeg must not target Owncast's loopback port directly. The reviewed private transport is:

`middleware -> 10.0.0.73:19361 -> desktop source-restricted socat relay -> 127.0.0.1:1936 -> Owncast`

The destination id is `owncast-desktop`, the secret reference is `NABEEL_OWNCAST_STREAM_KEY`, and the example remains `enabled: false`. The stream key is never committed and the private relay only accepts `10.0.0.220/32`.
