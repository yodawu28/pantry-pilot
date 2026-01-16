# Shared Package

Common Pydantic types used across all modules (API, Agent, MCP).

## Types

- `OCRStatus` - Receipt processing status enum
- `ReceiptMetadata` - Extracted merchant, date, total
- `LineItem` - Individual product item
- `ValidationResult` - Validation output
- `ExtractionResult` - Complete agent response
- `ImageData` - Image from storage
- `ReceiptContext` - Historical data for agent

## Installation

```bash
cd packages/shared
uv pip install -e .
```