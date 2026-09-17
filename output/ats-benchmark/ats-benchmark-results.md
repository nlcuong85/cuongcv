# ATS Benchmark

This benchmark compares the local MCP ATS approximation against the eight observed NodeFlair ATS scores captured during manual testing.

| Case | NodeFlair | Local | Delta | Profile | Status |
| --- | ---: | ---: | ---: | --- | --- |
| mercedes-process-development | 21 | 21 | 0 | mercedes_process_development | pass |
| mercedes-requirements-engineering | 45 | 50 | 5 | mercedes_requirements_engineering | pass |
| realworld-one-solution-delivery | 66 | 66 | 0 | solution_delivery | pass |
| 4flow-ai-consulting | 35 | 35 | 0 | ai_consulting | pass |
| appliedai-instructional-design | 66 | 66 | 0 | instructional_design | pass |
| sap-technical-writing | 30 | 30 | 0 | technical_writing | pass |
| schwarz-it-marketing-systems | 42 | 42 | 0 | ecommerce_marketing_systems | pass |
| vishay-controlling | 57 | 57 | 0 | controlling | pass |

Tolerance: ±8 points per case. NodeFlair's private engine is not public, so the local gate is calibrated to observed behavior and must be rerun after ATS rule changes.
