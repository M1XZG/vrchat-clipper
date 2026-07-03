# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Report it privately through
GitHub's **Report a vulnerability** button on the repository's
[Security tab](https://github.com/M1XZG/vrchat-clipper/security/advisories/new). That
opens a private advisory with the maintainer.

I'll acknowledge the report as soon as I can and work with you on a fix and a
coordinated disclosure.

## Scope and expectations

vrchat-clipper runs a small local server that drives OBS and VRChat on the same
machine. By default the server binds to loopback (`127.0.0.1`), so it is only
reachable from your own PC. If you change `server.host` to expose it on your network,
you take on the responsibility for securing that — the API has no authentication and
is designed for local use.

The most useful reports concern things like the server being reachable when it
shouldn't be, handling of the OBS WebSocket password in `config.json`, or the guided
installer touching files it shouldn't.
