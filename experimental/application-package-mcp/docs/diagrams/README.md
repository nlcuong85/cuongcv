# Diagram sources

Current website diagrams are maintained under `resources/diagrams/` and published as matching source/SVG pairs on `/assets/`.

- [Current bootstrap source](../../resources/diagrams/bootstrap-scaffolding-flow.puml): client connection and local-folder preconditions, kit setup and manifest audit.
- [Current review source](../../resources/diagrams/private-checker-flow.puml): selected writing or CV/JD checks, feedback and local release gates.
- [Current workflow source](../../resources/diagrams/local-first-human-flow.puml): local application workflow overview; retained downloadable asset.
- [Live technical explanation](https://jobmcp.pmlecuong.com/technical-flow). Local changes appear there only after deployment.

`local-first-mcp-application-flow.puml` and its SVG are explicitly historical: they record the early distribution-only design and must not be used as the current checker/privacy contract.

`optional-auth/` belongs to the separate proposed account-path plan. Anonymous onboarding changes do not implement or redesign that plan.

Edit canonical PlantUML, syntax-check, regenerate matching SVG, inspect a raster preview, and verify the source/image routes and nearby accessible explanations. The beginner four-step visual on `/start` is native HTML/CSS, so users need no diagram plugin or renderer service.
