# Owncast desktop authority

Owncast is **not** hosted on the middleware server.

Canonical runtime:
- host: `codestra-desktop` (`10.0.0.73`)
- Owncast web/API: `127.0.0.1:18080` on the desktop
- private API gateway: `10.0.0.73:18181`, restricted to `codestra-server` (`10.0.0.220`)
- Codestra Video Controller: `127.0.0.1:18100` on the middleware server
- signed webhook receiver: `10.0.0.220:18110/webhooks/owncast`

MediaMTX remains the middleware server's local media router. Owncast **control**
uses the authenticated desktop integration API gateway. Media delivery to
Owncast is a separate RTMP transport and remains disabled until the desktop's
actual loopback RTMP listener is re-read and staging-certified.

Do not install or enable a second Owncast runtime on the middleware server.
Do not expose Owncast's native HTTP/admin surface to the LAN.
External/public streaming remains default-deny until staging certification and
separate production approval.
