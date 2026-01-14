# MCP Tools Design — Receipt Extraction Agent

## Overview

This document defines the Model Context Protocol (MCP) tools that the LLM agent (Gemma-3n) will use to extract and process receipt data.

**Agent Goal:** Extract structured data from receipt images and store in database

**LLM Model:** Gemma-3n (multimodal, can process images directly)

---

## Tool 1: `extract_receipt_metadata`

**Purpose:** Extract high-level receipt information (merchant, date, total)

**Input Schema:**
```json
{
  "receipt_text": "string (raw OCR text or image description)",
  "receipt_id": "integer (database ID)"
}
```

**Output Schema:**
```json
{
  "merchant_name": "string | null",
  "purchase_date": "YYYY-MM-DD | null",
  "total_amount": "decimal | null",
  "currency": "string (default: USD)",
  "tax_amount": "decimal | null",
  "subtotal": "decimal | null",
  "confidence": "float (0.0-1.0)"
}
```

**Example:**
```json
Input:
{
  "receipt_text": "WHOLE FOODS MARKET\n01/10/2026\nTOTAL: $45.67",
  "receipt_id": 123
}

Output:
{
  "merchant_name": "Whole Foods Market",
  "purchase_date": "2026-01-10",
  "total_amount": 45.67,
  "currency": "USD",
  "tax_amount": null,
  "subtotal": null,
  "confidence": 0.95
}
```

**Tool Implementation:**
- Parse LLM's structured response
- Validate date format
- Validate amount > 0
- Return to agent for confirmation

---

## Tool 2: `extract_line_items`

**Purpose:** Extract individual products/items from receipt

**Input Schema:**
```json
{
  "receipt_text": "string",
  "receipt_id": "integer"
}
```

**Output Schema:**
```json
{
  "items": [
    {
      "item_name": "string",
      "quantity": "decimal | null",
      "unit_price": "decimal | null",
      "total_price": "decimal",
      "line_number": "integer"
    }
  ],
  "confidence": "float"
}
```

**Example:**
```json
Input:
{
  "receipt_text": "Organic Bananas  $3.99\nChicken Breast   $12.45\nMilk 2%          $4.50",
  "receipt_id": 123
}

Output:
{
  "items": [
    {
      "item_name": "Organic Bananas",
      "quantity": null,
      "unit_price": null,
      "total_price": 3.99,
      "line_number": 1
    },
    {
      "item_name": "Chicken Breast",
      "quantity": null,
      "unit_price": null,
      "total_price": 12.45,
      "line_number": 2
    },
    {
      "item_name": "Milk 2%",
      "quantity": null,
      "unit_price": null,
      "total_price": 4.50,
      "line_number": 3
    }
  ],
  "confidence": 0.92
}
```

---

## ~~Tool 3: `categorize_item`~~ (FUTURE/SEPARATE AGENT)

**Status:** Not included in initial MCP tools. May be handled by:
- Gemma-3n vision model directly (analyzing product images from receipt)
- Separate specialized categorization agent
- Rule-based post-processing (W03+)

**Purpose:** Assign food category to an item

**⚠️ IMPLEMENTATION NOTE:** Use **embedding similarity** or **keyword matching**, NOT LLM generation. Small models can hallucinate categories.

**Input Schema:**
```json
{
  "item_name": "string"
}
```

**Output Schema:**
```json
{
  "category_id": "integer | null",
  "category_name": "string",
  "match_score": "float (0.0-1.0)",
  "match_method": "string (exact/fuzzy/embedding/default)"
}
```

**Example:**
```json
Input: { "item_name": "Chicken Breast" }
Output: { 
  "category_id": 2, 
  "category_name": "Meat",
  "match_score": 0.98,
  "match_method": "keyword"
}

Input: { "item_name": "Organic Bananas" }
Output: { 
  "category_id": 6, 
  "category_name": "Fruits",
  "match_score": 0.95,
  "match_method": "keyword"
}
```

**Implementation Strategy:**

**Option 1: Keyword-Based Matching (Recommended for W02)**
```python
CATEGORY_KEYWORDS = {
    1: ["lettuce", "spinach", "kale", "broccoli", "carrot", "tomato"],  # Vegetables
    2: ["chicken", "beef", "pork", "lamb", "steak", "ground"],          # Meat
    3: ["milk", "cheese", "yogurt", "butter", "cream"],                 # Dairy
    4: ["salmon", "tuna", "shrimp", "fish", "seafood"],                 # Seafood
    6: ["banana", "apple", "orange", "grape", "berry"],                 # Fruits
}

def categorize_item(item_name: str):
    item_lower = item_name.lower()
    
    for category_id, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in item_lower:
                category = db.query(ItemCategory).get(category_id)
                return {
                    "category_id": category_id,
                    "category_name": category.name,
                    "match_score": 0.95,
                    "match_method": "keyword"
                }
    
    # Default fallback
    return {
        "category_id": None,
        "category_name": "Uncategorized",
        "match_score": 0.0,
        "match_method": "default"
    }
```

**Option 2: Embedding Similarity (Future - W04+)**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Pre-compute category embeddings
category_embeddings = {
    "Vegetables": model.encode("vegetables greens produce"),
    "Meat": model.encode("meat chicken beef pork protein"),
    "Dairy": model.encode("milk cheese yogurt dairy"),
}

def categorize_item(item_name: str):
    item_embedding = model.encode(item_name)
    
    best_match = None
    best_score = 0.0
    
    for category, emb in category_embeddings.items():
        score = cosine_similarity(item_embedding, emb)
        if score > best_score:
            best_score = score
            best_match = category
    
    return {
        "category_name": best_match,
        "match_score": best_score,
        "match_method": "embedding"
    }
```

**Fallback Chain:**
1. Exact match in product database
2. Keyword matching
3. Embedding similarity (if enabled)
4. Ask user to categorize (show top 3 suggestions)

---

## ~~Tool 4: `estimate_expiration_date`~~ (FUTURE/SEPARATE AGENT)

**Status:** Not included in initial MCP tools. This belongs to a separate **pantry management agent** (W03+) that handles inventory tracking and expiration monitoring.

**Purpose:** Estimate expiration date based on product type and purchase date

**⚠️ IMPORTANT:** This tool uses a **deterministic rule-based system**, NOT the LLM. Gemma-3n is too small for reliable food safety knowledge and may hallucinate shelf life data.

**Input Schema:**
```json
{
  "item_name": "string",
  "category_id": "integer",
  "purchase_date": "YYYY-MM-DD"
}
```

**Output Schema:**
```json
{
  "expiration_date": "YYYY-MM-DD",
  "shelf_life_days": "integer",
  "storage_recommendation": "string (fridge/freezer/pantry)",
  "source": "string (rule-based/database/default)"
}
```

**Example:**
```json
Input: {
  "item_name": "Chicken Breast",
  "category_id": 2,
  "purchase_date": "2026-01-10"
}

Output: {
  "expiration_date": "2026-01-17",
  "shelf_life_days": 7,
  "storage_recommendation": "fridge",
  "source": "category-rule"
}
```

**Implementation Strategy:**

**Option 1: Category-Based Rules (Recommended for W02)**
```python
SHELF_LIFE_RULES = {
    # category_id: (days, storage)
    1: (5, "fridge"),    # Vegetables (leafy greens)
    2: (7, "fridge"),    # Meat (fresh)
    3: (14, "fridge"),   # Dairy
    4: (3, "fridge"),    # Seafood
    5: (365, "pantry"),  # Grains (dry)
    6: (10, "counter"),  # Fruits
    7: (730, "pantry"),  # Condiments
    8: (30, "pantry"),   # Beverages
}

def estimate_expiration_date(item_name, category_id, purchase_date):
    days, storage = SHELF_LIFE_RULES.get(category_id, (14, "fridge"))  # default
    expiration = purchase_date + timedelta(days=days)
    return {
        "expiration_date": expiration,
        "shelf_life_days": days,
        "storage_recommendation": storage,
        "source": "category-rule"
    }
```

**Option 2: Product Database Lookup (Future - W03+)**
```python
# Create a product_shelf_life table
CREATE TABLE product_shelf_life (
  id SERIAL PRIMARY KEY,
  product_name VARCHAR(255),
  category_id INTEGER,
  shelf_life_days INTEGER,
  storage_type VARCHAR(50),
  source VARCHAR(100)  -- USDA, FDA, manufacturer
);

# Lookup by item name with fuzzy matching
def estimate_expiration_date(item_name, category_id, purchase_date):
    # Try exact match first
    product = db.query(product_shelf_life).filter(
        func.lower(product_name) == item_name.lower()
    ).first()
    
    # Fallback to category rule
    if not product:
        days, storage = SHELF_LIFE_RULES[category_id]
    else:
        days = product.shelf_life_days
        storage = product.storage_type
    
    return {...}
```

**Option 3: USDA Food Safety API (Future)**
```python
# Query external food safety database
response = requests.get(
    "https://api.foodsafety.gov/shelf-life",
    params={"product": item_name, "category": category_name}
)
```

**Fallback Chain:**
1. Try product database lookup (exact match)
2. Try fuzzy match on product name
3. Use category-based rule
4. Use conservative default (7 days, fridge)

**Safety Margin:**
- Always use conservative estimates (shorter shelf life)
- Never exceed maximum safe storage time
- Add configurable safety margin (e.g., -1 day buffer)

---

## Tool 3: `validate_extraction`

**Purpose:** Validate extracted data against business rules

**Input Schema:**
```json
{
  "receipt_data": {
    "total_amount": "decimal",
    "items": "array",
    "purchase_date": "YYYY-MM-DD"
  }
}
```

**Output Schema:**
```json
{
  "valid": "boolean",
  "warnings": "array of strings",
  "errors": "array of strings"
}
```

**Validation Rules:**
- Sum of item prices should approximately equal total_amount (±5% tolerance)
- Purchase date not in future
- All amounts positive
- At least one item extracted
- Merchant name not empty

**Example:**
```json
Input: {
  "receipt_data": {
    "total_amount": 45.67,
    "items": [
      {"total_price": 12.45},
      {"total_price": 33.22}
    ],
    "purchase_date": "2026-01-10"
  }
}

Output: {
  "valid": true,
  "warnings": [],
  "errors": []
}
```

---

## Agent Workflow

**Pure Extraction Flow:**

```
1. API receives receipt image from user
   ↓
2. API calls Agent with image
   ↓
3. Agent calls: extract_receipt_metadata
   ← Returns: merchant, date, total
   ↓
4. Agent calls: extract_line_items
   ← Returns: list of items with prices
   ↓
5. Agent calls: validate_extraction
   ← Returns: validation result
   ↓
6. Agent returns JSON response to API:
   {
     "metadata": {...},
     "items": [...],
     "validation": {...}
   }
   ↓
7. API independently saves to database
   ↓
8. API returns result to frontend
   (User can review/edit in UI)
```

**Notes on Categorization:**
- **Option A:** Gemma-3n may categorize items during `extract_line_items` using vision context (e.g., seeing chicken breast in receipt photo)
- **Option B:** Separate categorization agent processes saved receipts in background (W03+)
- **Option C:** User manually categorizes during review step

**Notes on Expiration Dates:**
- Not handled by this agent - belongs to separate pantry management workflow (W03+)

---

## Error Handling

**Low Confidence (<0.7):**
- Flag for manual review
- Show extracted data to user for correction
- Don't auto-save to pantry

**Validation Failures:**
- Return errors to agent
- Agent retries with corrections
- Max 3 retry attempts

**Tool Failures:**
- Database errors: retry with exponential backoff
- Network errors: queue for later processing
- Invalid input: return clear error message to agent

---

## Agent Final Output

The agent returns a **structured JSON response** to the API, which then handles database persistence independently.

**Response Schema:**
```json
{
  "status": "success | failed",
  "metadata": {
    "merchant_name": "string | null",
    "purchase_date": "YYYY-MM-DD | null",
    "total_amount": "decimal | null",
    "currency": "string",
    "confidence": "float (0.0-1.0)"
  },
  "items": [
    {
      "item_name": "string",
      "quantity": "decimal | null",
      "unit_price": "decimal | null",
      "total_price": "decimal",
      "line_number": "integer",
      "confidence": "float (0.0-1.0)"
    }
  ],
  "validation": {
    "valid": "boolean",
    "warnings": ["array of strings"],
    "errors": ["array of strings"]
  },
  "processing_time_ms": "integer",
  "agent_version": "string"
}
```

**Example Success Response:**
```json
{
  "status": "success",
  "metadata": {
    "merchant_name": "Whole Foods Market",
    "purchase_date": "2026-01-10",
    "total_amount": 45.67,
    "currency": "USD",
    "confidence": 0.92
  },
  "items": [
    {
      "item_name": "Organic Bananas",
      "quantity": 1.5,
      "unit_price": 1.50,
      "total_price": 2.25,
      "line_number": 1,
      "confidence": 0.95
    },
    {
      "item_name": "Chicken Breast",
      "quantity": null,
      "unit_price": null,
      "total_price": 12.45,
      "line_number": 2,
      "confidence": 0.88
    }
  ],
  "validation": {
    "valid": true,
    "warnings": ["Total amount mismatch: sum(items)=14.70, total=45.67"],
    "errors": []
  },
  "processing_time_ms": 3247,
  "agent_version": "gemma-3n-v1.0"
}
```

**Example Failure Response:**
```json
{
  "status": "failed",
  "metadata": null,
  "items": [],
  "validation": {
    "valid": false,
    "warnings": [],
    "errors": ["No text detected in image", "Receipt too blurry"]
  },
  "processing_time_ms": 1532,
  "agent_version": "gemma-3n-v1.0"
}
```

**API Workflow After Receiving Agent Response:**
1. Receive JSON from agent
2. If `status == "success"` and `validation.valid == true`:
   - Save metadata to `receipts` table
   - Save items to `receipt_items` table (future)
   - Update `ocr_status` to 'completed'
3. If failed or invalid:
   - Update `ocr_status` to 'failed'
   - Store error messages
4. Return response to frontend

---

## MCP Server Implementation

**Technology:**
- Framework: FastMCP or custom MCP server
- Language: Python (same as API)
- Deployment: Same container as API or separate service

**Example Tool Registration:**
```python
from mcp import MCPServer, Tool

server = MCPServer()

@server.tool()
async def extract_receipt_metadata(receipt_text: str, receipt_id: int):
    """Extract merchant, date, and total from receipt"""
    # Implementation here
    return {
        "merchant_name": "...",
        "purchase_date": "...",
        "total_amount": 0.0,
        "confidence": 0.95
    }

@server.tool()
async def categorize_item(item_name: str):
    """Assign category to food item"""
    # Query database or use ML model
    return {
        "category_id": 1,
        "category_name": "Vegetables",
        "confidence": 0.90
    }
```

---

## Performance Considerations

**Optimization:**
- Cache category lookups (Redis)
- Batch database inserts
- Parallel tool calls when possible
- Stream results back to user

**Latency Target:**
- Total extraction: <10 seconds per receipt
- Tool calls: <500ms each
- Database operations: <100ms

---

## Security

**Input Validation:**
- Sanitize receipt_text before processing
- Validate receipt_id exists in database
- Check user permissions

**Rate Limiting:**
- Max 10 receipts per minute per user
- Tool call rate limiting

**Data Privacy:**
- Don't log sensitive receipt data
- Encrypt receipt images at rest
- Delete raw OCR text after 30 days (optional)

---

## Future Enhancements

**W03+:**
- `detect_duplicate_items` tool
- `suggest_recipe` based on pantry items
- `price_comparison` with historical data
- `nutritional_info_lookup` tool

**Advanced:**
- Multi-language support
- Handwritten receipt parsing
- Receipt fraud detection
- Automatic pantry restocking suggestions
