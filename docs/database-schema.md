# Database Schema — PantryPilot

This document defines all database tables, columns, indexes, and relationships for PantryPilot.

**Technology:** PostgreSQL 16 with SQLAlchemy 2.0 (async)

**Migration Tool:** Alembic

---

## Tables Overview

| Table              | Status | Week | Description                          |
|--------------------|--------|------|--------------------------------------|
| users              | ✅ Live | W01  | User accounts                        |
| receipts           | ✅ Live | W01  | Receipt metadata and parsed data     |
| receipt_items      | 📋 Planned | W03+ | Individual line items from receipts  |
| pantry_items       | 📋 Planned | W04+ | Current pantry inventory tracking    |
| item_categories    | 📋 Planned | W03+ | Product categories (vegetables, meat, etc.) |

---

## Table: `users`

**Purpose:** Store user account information

**Status:** ✅ Implemented in W01

| Column      | Type                 | Nullable | Default    | Index | Constraints | Description              |
|-------------|----------------------|----------|------------|-------|-------------|--------------------------|
| id          | INTEGER              | NO       | AUTO       | PK    | PRIMARY KEY | User ID                  |
| email       | VARCHAR              | NO       | -          | UNIQUE| UNIQUE      | User email address       |
| name        | VARCHAR              | NO       | -          | -     | -           | User display name        |
| created_at  | TIMESTAMP WITH TZ    | NO       | now()      | -     | -           | Account creation time    |
| updated_at  | TIMESTAMP WITH TZ    | NO       | now()      | -     | -           | Last update time         |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`

**Sample Data:**
```sql
INSERT INTO users (id, email, name) VALUES 
  (1, 'test@example.com', 'Test User');
```

---

## Table: `receipts`

**Purpose:** Store receipt metadata, images, and parsed OCR data

**Status:** ✅ Implemented in W01, 📋 W02 extensions planned

| Column         | Type                 | Nullable | Default      | Index | Constraints          | Description                      |
|----------------|----------------------|----------|--------------|-------|----------------------|----------------------------------|
| id             | INTEGER              | NO       | AUTO         | PK    | PRIMARY KEY          | Receipt ID                       |
| user_id        | INTEGER              | NO       | -            | FK    | FOREIGN KEY(users)   | Owner user ID                    |
| image_path     | VARCHAR              | NO       | -            | -     | -                    | MinIO object path                |
| purchase_date  | DATE                 | NO       | -            | -     | -                    | Date of purchase                 |
| status         | VARCHAR              | NO       | 'uploaded'   | -     | -                    | Receipt status                   |
| ocr_status     | VARCHAR              | YES      | 'pending'    | -     | W02                  | OCR processing status            |
| ocr_text       | TEXT                 | YES      | NULL         | -     | W02                  | Raw OCR extracted text           |
| merchant_name  | VARCHAR(255)         | YES      | NULL         | -     | W02                  | Parsed merchant name             |
| total_amount   | DECIMAL(10,2)        | YES      | NULL         | -     | W02                  | Parsed total amount              |
| currency       | VARCHAR(3)           | YES      | 'USD'        | -     | W02                  | Currency code (ISO 4217)         |
| parsed_at      | TIMESTAMP WITH TZ    | YES      | NULL         | -     | W02                  | When OCR completed               |
| created_at     | TIMESTAMP WITH TZ    | NO       | now()        | -     | -                    | Record creation time             |
| updated_at     | TIMESTAMP WITH TZ    | YES      | NULL         | -     | -                    | Last update time                 |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id` (foreign key + filtering)

**Foreign Keys:**
- `user_id` → `users.id` ON DELETE CASCADE

**Status Enum Values:**
- `uploaded` - Image uploaded successfully
- `processing` - OCR in progress
- `processed` - OCR completed successfully
- `failed` - Upload or OCR failed

**OCR Status Enum Values (W02):**
- `pending` - Not yet processed
- `processing` - OCR in progress
- `completed` - Successfully extracted and parsed
- `failed` - OCR or parsing failed

**Sample Data:**
```sql
INSERT INTO receipts (user_id, image_path, purchase_date, status, merchant_name, total_amount, currency) VALUES 
  (1, 'minio://receipts/receipt_001.jpg', '2026-01-10', 'uploaded', 'Whole Foods Market', 45.67, 'USD');
```

---

## Table: `receipt_items` (Planned - W03+)

**Purpose:** Store individual line items from parsed receipts

**Status:** 📋 Planned for future implementation

| Column         | Type                 | Nullable | Default | Index | Constraints             | Description                   |
|----------------|----------------------|----------|---------|-------|-------------------------|-------------------------------|
| id             | INTEGER              | NO       | AUTO    | PK    | PRIMARY KEY             | Line item ID                  |
| receipt_id     | INTEGER              | NO       | -       | FK    | FOREIGN KEY(receipts)   | Parent receipt ID             |
| item_name      | VARCHAR(255)         | NO       | -       | -     | -                       | Product/item name             |
| quantity       | DECIMAL(10,3)        | YES      | NULL    | -     | -                       | Quantity purchased            |
| unit_price     | DECIMAL(10,2)        | YES      | NULL    | -     | -                       | Price per unit                |
| total_price    | DECIMAL(10,2)        | NO       | -       | -     | -                       | Total line item cost          |
| category_id    | INTEGER              | YES      | NULL    | FK    | FOREIGN KEY(categories) | Item category                 |
| expiration_date| DATE                 | YES      | NULL    | -     | -                       | Best before / expiry date     |
| created_at     | TIMESTAMP WITH TZ    | NO       | now()   | -     | -                       | Record creation time          |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `receipt_id` (foreign key + filtering)
- INDEX on `category_id` (foreign key + filtering)
- INDEX on `expiration_date` (for finding items expiring soon)

**Foreign Keys:**
- `receipt_id` → `receipts.id` ON DELETE CASCADE
- `category_id` → `item_categories.id` ON DELETE SET NULL

**Notes:**
- `expiration_date`: Critical for pantry management - prioritize using items expiring soonest
- `category_id`: Links to predefined categories (vegetables, meat, dairy, etc.)
- Example use case: User buys pork on 2 receipts with different expiry dates → stored as 2 separate receipt_items

---

## Table: `item_categories` (Planned - W03+)

**Purpose:** Categorize food items for better organization and tracking

**Status:** 📋 Planned for future implementation

| Column         | Type                 | Nullable | Default | Index | Constraints             | Description                   |
|----------------|----------------------|----------|---------|-------|-------------------------|-------------------------------|
| id             | INTEGER              | NO       | AUTO    | PK    | PRIMARY KEY             | Category ID                   |
| name           | VARCHAR(100)         | NO       | -       | UNIQUE| UNIQUE                  | Category name                 |
| parent_id      | INTEGER              | YES      | NULL    | FK    | FOREIGN KEY(self)       | Parent category (hierarchy)   |
| icon           | VARCHAR(50)          | YES      | NULL    | -     | -                       | Icon name/emoji               |
| created_at     | TIMESTAMP WITH TZ    | NO       | now()   | -     | -                       | Record creation time          |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `name`
- INDEX on `parent_id` (for hierarchical queries)

**Foreign Keys:**
- `parent_id` → `item_categories.id` (self-referencing for subcategories)

**Sample Categories:**
```sql
INSERT INTO item_categories (id, name, parent_id, icon) VALUES 
  (1, 'Vegetables', NULL, '🥬'),
  (2, 'Meat', NULL, '🥩'),
  (3, 'Dairy', NULL, '🥛'),
  (4, 'Seafood', NULL, '🐟'),
  (5, 'Grains', NULL, '🌾'),
  (6, 'Fruits', NULL, '🍎'),
  (7, 'Condiments', NULL, '🧂'),
  (8, 'Beverages', NULL, '🥤'),
  -- Subcategories
  (10, 'Leafy Greens', 1, '🥬'),
  (11, 'Root Vegetables', 1, '🥕'),
  (12, 'Poultry', 2, '🍗'),
  (13, 'Red Meat', 2, '🥩'),
  (14, 'Pork', 2, '🥓');
```

---

## Table: `pantry_items` (Planned - W04+)

**Purpose:** Track current pantry inventory with expiration dates and quantities

**Status:** 📋 Planned for future implementation

**Use Case:** After parsing receipts, items are added to pantry. Users can track what they have, quantities, and expiration dates to minimize waste.

| Column            | Type                 | Nullable | Default     | Index | Constraints             | Description                      |
|-------------------|----------------------|----------|-------------|-------|-------------------------|----------------------------------|
| id                | INTEGER              | NO       | AUTO        | PK    | PRIMARY KEY             | Pantry item ID                   |
| user_id           | INTEGER              | NO       | -           | FK    | FOREIGN KEY(users)      | Owner user ID                    |
| receipt_item_id   | INTEGER              | YES      | NULL        | FK    | FOREIGN KEY(receipt_items) | Source receipt item           |
| item_name         | VARCHAR(255)         | NO       | -           | -     | -                       | Product/item name                |
| category_id       | INTEGER              | YES      | NULL        | FK    | FOREIGN KEY(categories) | Item category                    |
| quantity_current  | DECIMAL(10,3)        | NO       | -           | -     | CHECK (>= 0)            | Current quantity available       |
| quantity_unit     | VARCHAR(20)          | YES      | NULL        | -     | -                       | Unit (kg, lbs, pieces, etc.)     |
| expiration_date   | DATE                 | YES      | NULL        | -     | -                       | Best before / expiry date        |
| location          | VARCHAR(100)         | YES      | NULL        | -     | -                       | Storage location (fridge, freezer) |
| status            | VARCHAR(20)          | NO       | 'available' | -     | -                       | available, low, expired, consumed |
| added_at          | TIMESTAMP WITH TZ    | NO       | now()       | -     | -                       | When added to pantry             |
| consumed_at       | TIMESTAMP WITH TZ    | YES      | NULL        | -     | -                       | When fully consumed              |
| updated_at        | TIMESTAMP WITH TZ    | YES      | NULL        | -     | -                       | Last update time                 |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id` (filtering by user)
- INDEX on `category_id` (filtering by category)
- INDEX on `expiration_date` (finding items expiring soon)
- INDEX on `status` (filtering available items)
- COMPOSITE INDEX on `(user_id, status, expiration_date)` (common query pattern)

**Foreign Keys:**
- `user_id` → `users.id` ON DELETE CASCADE
- `receipt_item_id` → `receipt_items.id` ON DELETE SET NULL (preserve history)
- `category_id` → `item_categories.id` ON DELETE SET NULL

**Status Enum Values:**
- `available` - Item in stock and not expired
- `low` - Quantity below threshold
- `expired` - Past expiration date
- `consumed` - Fully used up

**Example Scenario:**
```
User buys pork on Jan 1 (expires Jan 15) → receipt_item_1 → pantry_item_1
User buys pork on Jan 5 (expires Jan 20) → receipt_item_2 → pantry_item_2

Query for "use pork expiring soon":
SELECT * FROM pantry_items 
WHERE item_name LIKE '%pork%' 
  AND status = 'available'
  AND expiration_date IS NOT NULL
ORDER BY expiration_date ASC;

Result: pantry_item_1 (Jan 15) appears first, suggesting user should use it before pantry_item_2 (Jan 20)
```

---

## Schema Evolution

### W01 (Current)
- ✅ `users` table with basic fields
- ✅ `receipts` table with image storage and metadata

### W02 (Planned - OCR Integration)
- 📋 Add OCR columns to `receipts`:
  - `ocr_status` VARCHAR
  - `ocr_text` TEXT
  - `merchant_name` VARCHAR(255)
  - `total_amount` DECIMAL(10,2)
  - `currency` VARCHAR(3)
  - `parsed_at` TIMESTAMP WITH TZ

**Migration Script:**
```sql
-- W02 Migration: Add OCR fields
ALTER TABLE receipts
  ADD COLUMN ocr_status VARCHAR DEFAULT 'pending',
  ADD COLUMN ocr_text TEXT,
  ADD COLUMN merchant_name VARCHAR(255),
  ADD COLUMN total_amount DECIMAL(10,2),
  ADD COLUMN currency VARCHAR(3) DEFAULT 'USD',
  ADD COLUMN parsed_at TIMESTAMP WITH TIME ZONE;
```

### W03+ (Future)
- 📋 Create `receipt_items` table for line item parsing
  - Add `expiration_date` field for tracking best-before dates
  - Add `category_id` foreign key to categorize items
- 📋 Create `item_categories` table with hierarchical structure
  - Predefined categories: vegetables, meat, dairy, seafood, etc.
  - Support subcategories (e.g., poultry under meat)
- 📋 Create `pantry_items` table for inventory management
  - Track current quantities and expiration dates
  - Link to source receipt_items for traceability
  - Status tracking (available, low, expired, consumed)
- 📋 Add authentication-related tables (sessions, tokens)
- 📋 Add user preferences table

**Use Case - Expiration Tracking:**
```
Problem: User buys pork on 2 different days with different expiry dates
- Jan 1: Pork (2 lbs) - expires Jan 15
- Jan 5: Pork (1.5 lbs) - expires Jan 20

Solution: Store as separate pantry_items, query by expiration_date ASC
Result: App suggests using Jan 15 batch first to minimize waste
```

---

## Relationships

```
users (1) ──< (many) receipts
users (1) ──< (many) pantry_items

receipts (1) ──< (many) receipt_items

receipt_items (many) ──> (1) item_categories
receipt_items (1) ──── (0..1) pantry_items [optional link to track source]

pantry_items (many) ──> (1) item_categories
pantry_items (many) ──> (1) users

item_categories (1) ──< (many) item_categories [self-referencing hierarchy]
```

**Key Flows:**
1. **Receipt → Items**: When receipt is parsed, create receipt_items
2. **Items → Pantry**: User can add receipt_items to pantry inventory
3. **Expiration Tracking**: Query pantry_items ordered by expiration_date to prioritize usage
4. **Category Insights**: Aggregate spending/consumption by item_categories

---

## Data Types & Conventions

### Timestamps
- All timestamps use `TIMESTAMP WITH TIME ZONE`
- Default value: `now()` (server time)
- UTC recommended for storage

### Primary Keys
- Auto-incrementing INTEGER for all tables
- Consider UUID for distributed systems (future consideration)

### Foreign Keys
- All foreign keys have `ON DELETE CASCADE` or `ON DELETE SET NULL` based on business logic
- Foreign key columns are indexed for query performance

### String Lengths
- Email: VARCHAR (unlimited, but typically < 255)
- Names: VARCHAR(255)
- Currency codes: VARCHAR(3) (ISO 4217)
- Status fields: VARCHAR (short enum values)

### Decimal Precision
- Monetary amounts: DECIMAL(10,2) - supports up to 99,999,999.99
- Quantities: DECIMAL(10,3) - supports fractional quantities

---

## Indexes Strategy

### Current Indexes
1. Primary keys on all tables (automatic)
2. `users.email` - unique index for login lookups
3. `receipts.user_id` - foreign key index for user's receipt queries

### Future Indexes (W02+)
4. `receipts.merchant_name` - for filtering/grouping by merchant
5. `receipts.purchase_date` - for date range queries
6. `receipts.ocr_status` - for filtering by processing status
7. `receipt_items.receipt_id` - foreign key index

---

## Database Constraints

### CHECK Constraints (Future)
```sql
-- Ensure positive amounts
ALTER TABLE receipts 
  ADD CONSTRAINT check_positive_amount 
  CHECK (total_amount IS NULL OR total_amount > 0);

-- Ensure valid currency codes (basic check)
ALTER TABLE receipts 
  ADD CONSTRAINT check_currency_length 
  CHECK (currency IS NULL OR length(currency) = 3);

-- Ensure purchase_date not in future
ALTER TABLE receipts 
  ADD CONSTRAINT check_purchase_date 
  CHECK (purchase_date <= CURRENT_DATE);
```

---

## Seed Data

### Development Seed
```sql
-- Seed user for testing
INSERT INTO users (id, email, name) VALUES 
  (1, 'test@example.com', 'Test User')
ON CONFLICT (id) DO NOTHING;

-- Sample receipts
INSERT INTO receipts (user_id, image_path, purchase_date, status, merchant_name, total_amount, currency) VALUES 
  (1, 'minio://receipts/sample_001.jpg', '2026-01-10', 'uploaded', 'Trader Joes', 32.45, 'USD'),
  (1, 'minio://receipts/sample_002.jpg', '2026-01-09', 'uploaded', 'Whole Foods', 78.90, 'USD')
ON CONFLICT DO NOTHING;
```

---

## Maintenance Notes

### Backup Strategy
- Daily automated backups recommended
- Retention: 30 days for development, longer for production

### Migration Best Practices
1. Always create reversible migrations (up/down)
2. Test migrations on copy of production data
3. Use Alembic for version control
4. Add migrations to git repository

### Performance Considerations
- Monitor query performance on `receipts` table as it grows
- Consider partitioning by date if table exceeds 1M rows
- Regularly VACUUM and ANALYZE tables
- Monitor index usage with pg_stat_user_indexes

---

## Related Documentation
- [API Contracts](./api-contracts.md) - API endpoints using these tables
- [Architecture](./architecture.md) - Overall system design
- [W02 Plan](./plans/2026-W02-plan.md) - OCR schema extensions
