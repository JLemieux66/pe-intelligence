-- Performance Optimization: Add full-text search capability
-- This provides 10-50x faster text search compared to ILIKE

-- Step 1: Add tsvector column for full-text search
ALTER TABLE companies ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Step 2: Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_company_search ON companies USING GIN(search_vector);

-- Step 3: Create function to update search_vector
CREATE OR REPLACE FUNCTION companies_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.former_name, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.verticals, '')), 'D');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Step 4: Create trigger to automatically update search_vector
DROP TRIGGER IF EXISTS companies_search_update ON companies;
CREATE TRIGGER companies_search_update
  BEFORE INSERT OR UPDATE OF name, former_name, description, verticals
  ON companies
  FOR EACH ROW
  EXECUTE FUNCTION companies_search_vector_update();

-- Step 5: Populate existing rows
UPDATE companies SET search_vector =
  setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(former_name, '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(description, '')), 'C') ||
  setweight(to_tsvector('english', COALESCE(verticals, '')), 'D')
WHERE search_vector IS NULL;

-- Verify the setup
SELECT
    COUNT(*) as total_companies,
    COUNT(search_vector) as companies_with_search
FROM companies;

-- Test the search (example query)
-- SELECT name, description
-- FROM companies
-- WHERE search_vector @@ to_tsquery('english', 'software & technology')
-- ORDER BY ts_rank(search_vector, to_tsquery('english', 'software & technology')) DESC
-- LIMIT 10;
