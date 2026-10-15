# Security policy

The simulator never executes displayed terminal commands or mutates the host OS.
Do not expose the development server directly to the public internet; place it
behind an authenticated reverse proxy. Episode JSON contains hidden policies and
must remain private.

## Current development trust boundary

The v2 development server has no authentication or per-user authorization.
Its Studio and demo/practice/session-control APIs are trusted authoring surfaces,
not a secure public evaluation service. Knowing a session ID is not an access
control mechanism. Do not give a tested agent arbitrary HTTP, DOM, source-file,
episode-file or authoring access; a runner must expose only the intended desktop
pixels and allowed coordinate/keyboard actions, without browser navigation to
trusted routes. The source distribution intentionally contains generators and
scoring code for researchers and must not be mounted into the agent environment.

An authenticated parent/reverse proxy alone does not separate an agent from
authoring endpoints if both receive unrestricted access to the same origin.
The parent must enforce the visual-action boundary and keep trusted control
credentials, episode IDs, exports and hidden control-condition labels separate.
INTEGRATION.md documents current root-relative routes and same-origin messages;
cross-origin production proxy/authentication has not been validated here.

Static-file containment checks restrict served files to static assets and the
video artifact directory, including resolved symlink targets. They do not
independently verify artifact readiness or enforce per-session ownership. They
also do not provide
authorization or make hidden conventions secret against source/HTTP access.
Synthetic signing uses a public test authority, and stable pseudonyms are not
cryptographic anonymization. Use synthetic project data, not personal documents
or real credentials, in benchmark fixtures and distributed demonstrations.

Report vulnerabilities privately to the repository maintainers before public
disclosure. Include the affected version, reproduction steps, and impact.
