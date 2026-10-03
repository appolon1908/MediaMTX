# Owncast desktop authority

Owncast is **not** hosted on the middleware server.

Canonical runtime:
- host: `codestra-desktop` (`10.0.0.73`)
- Owncast web/API: `127.0.0.1:18080` on the desktop
- API bridge: `10.0.0.73:18180`, restricted to `codestra-server` (`10.0.0.220`)
- server connector: `127.0.0.1:18104`
- signed webhook ingress: `10.0.0.220:18184/v1/webhooks/owncast`

MediaMTX remains the middleware server's media router. The Owncast **control plane**
uses the authenticated API bridge; media payload delivery to Owncast uses its
RTMP ingest transport and is a separate, explicitly gated route.

Do not install or enable a second Owncast runtime on the middleware server.
External/public streaming remains disabled until staging certification and
separate production approval.
