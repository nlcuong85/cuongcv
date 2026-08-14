# Local development checkout

This directory is a source-only import of the Franklee `Student Application AI Helper` MCP service, captured on 2026-08-14 from `/DATA/AppData/application-package-mcp`.

It intentionally excludes Franklee runtime state: `data/`, `node_modules/`, temporary artifacts, Python bytecode, and the deployed classmate sample workspace. Do not add candidate data, generated packages, tokens, or production environment files here.

Run locally:

```bash
npm ci
npm test
npm run start:http
```

The local MCP endpoint is `http://127.0.0.1:5920/mcp`. The deployed service is `https://jobmcp.pmlecuong.com/mcp`.
