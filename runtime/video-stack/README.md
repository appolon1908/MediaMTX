# Video stack MediaMTX bridge

MediaMTX keeps its native Control API.

- Control API: `http://127.0.0.1:9997`
- Metrics: `http://127.0.0.1:9998`
- RTSP: `127.0.0.1:8554`
- RTMP: `127.0.0.1:19350`
- HLS: `127.0.0.1:18888`
- WebRTC HTTP: `127.0.0.1:18889`
- Only the `test` path is declared in this staging configuration.
- Public/external destinations remain disabled.

The controller must use the native `/v3/*` API rather than a duplicate MediaMTX service.
