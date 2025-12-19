# PRD: Finance-Insight (Financial Logic Overlay Engine)

## Project Vision
A metadata-driven calculation engine that allows Finance users to define "Alternate Hierarchies" and "Business Logic Overlays" atop official GL data.

## Core Features (MVP 1)
- **Hierarchy Management**: Support for ragged alternate structures.
- **Top-Down Overrides**: Parent-level rules supersede child rollups.
- **The Reconciliation Plug**: Automatic generation of balancing rows: `Plug = Parent_Custom - SUM(Children_Natural)`.
- **Multi-Measure Support**: Single rule applies to Daily, MTD, YTD, and PYTD.
- **GenAI Rule Builder**: Natural Language to JSON logic via Gemini 1.5 Pro.

