# Job MCP Security Intake — 2026-10-18

## Decision

**APPROVED FOR DEPLOYMENT for the requested compatibility repair.** The release adds no new tools, privileges, credentials, network destinations, or data persistence. The owner explicitly asked to fix the modern `server/discover` failure. The intentionally public, unauthenticated service policy is unchanged.

## Scope and identity

- Source: `https://github.com/nlcuong85/cuongcv.git`
- Production checkout: `/DATA/AppData/application-package-mcp`
- Deployed source commit: `dc17719fc25f9af8284cc34a97d7e3d19ab9414a` (Job MCP implementation commit: `b5572084aec8e7c5b83ec30a3c0137214d4bae11`)
- Service version: `0.2.20`
- Production image ID: `sha256:3f2e06d27040a4c45c138094f6298fbe50031026266ad8d047c867cae94e02d0`
- Risk tier: **Tier 4** (public MCP service that accepts selected user text for transient checks)

## Changes and trust boundary

The service moved from the v1 TypeScript SDK to the official split v2 packages. `createMcpHandler` and the Node adapter support both modern 2026-07-28 requests and legacy 2025 `initialize` requests. The 64 KiB request limit, pre-existing authorization check, tool inventory, transient text handling, and aggregate-only `MCP_METRIC` logging remain in place. No client text, request/response body, IP address, or session ID is added to logs.

Pinned dependencies and npm lockfile integrity values:

- `@modelcontextprotocol/server@2.3.1` — `sha512-e59MfWuSssj6DoQ96JCTqdW1AXT5/XtnTl0WWd6MU1Ka434fFUGGosCLJbGNySDhHGvxQWoRWK137FXYFkYNWw==`
- `@modelcontextprotocol/node@2.1.1` — `sha512-EY92OAXN2xYL7tNS/MVsWJW1v8VHAPwl9B4Ca3pCrjmvqyC+S1C/6UHsMxF2GoFPraS5Yyg56vFz9brVpFojMA==`
- `@modelcontextprotocol/client@2.3.1` (test-only) — `sha512-mIGZXpHsjnZ6lD+gD/WCMpR5k8yVQQ8nNFH1N0Srf7AvnwTUMYD6pvTY8ng2+He5FfV7YMZLmrjL7cLa/cc3dQ==`
- SBOM: [security/sbom-0.2.20.cdx.json](security/sbom-0.2.20.cdx.json), SHA-256 `eabb085a707987298633a7a6a9cf1151bb44f9ec9d877053f23e88ec764471f9`

Package metadata and tarball integrity were checked against npm. The dependency install used `--ignore-scripts` locally; production `npm ci` reported zero vulnerabilities. No package signature or provenance attestation was verified. The old dependency tree was replaced; the new full and production `npm audit` both report zero findings.

## Review and verification evidence

- Reviewed the changed HTTP dispatch, authorization-before-MCP path, body-size limit, telemetry fields, package scripts, lockfile, Dockerfile, Compose service, and repository workflow. No new secret, shell execution, filesystem write, upload, or URL-fetch path was introduced.
- `npm test`: 6 passed, 0 failed. Includes a legacy client and an auto-negotiating modern client; modern discovery, tool listing, and health call passed.
- Local application-kit regression: all 3 sample cases passed after pointing the runner at an isolated local service on port 5943. The earlier attempt without that local service failed its selected-text review calls; it did not change the samples or production data.
- `npm audit --omit=dev` and `npm audit`: 0 vulnerabilities.
- Production `npm ci` and Docker build completed with 0 reported vulnerabilities.
- Public smoke test against `https://jobmcp.pmlecuong.com/mcp` passed both protocol eras and confirmed all 11 tools.
- Internal and public `/health` returned version `0.2.20`; health reports `tokenRequired:false`, unchanged from before deployment.
- Production `MCP_METRIC` records showed `server/discover` HTTP 200 followed by `tools/list` HTTP 200. Metrics continue to contain only operation/tool name, status, timestamp, and duration.
- Dashboard UI was checked at a 390 px viewport: the page remained within the viewport and the wide operations table scrolled inside its own wrapper. The table displayed operation descriptions with no browser console errors.
- The existing GitHub Actions workflow deploys the CV website, not the Job MCP container. It was not changed; its third-party actions use version tags rather than full commit SHAs, and that inherited workflow was not part of this container release.

## Existing exposure and residual risk

- The service remains publicly reachable and unauthenticated by design (`tokenRequired:false`). The current patch does not add rate limiting or source attribution. A caller can still make anonymous requests, including compute-bearing writing and ATS checks. This exposure predates the patch and is unchanged; dashboard telemetry cannot identify individual callers.
- The historic `server/discover` failures are now explained by a protocol mismatch: the old server implemented only the legacy `initialize` flow. The first modern probe after deployment succeeded. Earlier failures cannot be attributed to a particular caller because source IPs and request bodies are intentionally not retained.
- The SDK packages require Node 20+, matching the production image base (`node:20-alpine`). Image base tags are mutable; the deployed image ID above is the immutable runtime identity. No registry provenance for the base image was collected for this repair.

## Rollback

- Production Git rollback tag: `pre-jobmcp-v0.2.19-20261018` at previous source commit `6f34c093b82deecbc022bff4234cb39d927439c0`.
- Pre-deploy Compose and Dockerfile backup: `/root/deploy-backups/jobmcp-20261018-pre-v0.2.20/`.
- Previous running image ID is recorded in that directory's `predeploy.txt`; no database or user-file data was migrated.

To roll back, check out the rollback tag in the production source checkout, then rebuild and recreate only `application-package-mcp` with its Compose file. Preserve both untracked `.env` files.
