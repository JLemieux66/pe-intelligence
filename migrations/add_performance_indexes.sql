-- Performance Optimization: Add missing indexes
-- Run this migration to add indexes for better query performance

-- Add index on primary_industry_sector (used in similar companies filtering)
CREATE INDEX IF NOT EXISTS idx_primary_sector ON companies(primary_industry_sector);

-- Add composite index for country + sector (used in similarity queries)
CREATE INDEX IF NOT EXISTS idx_country_sector ON companies(country, primary_industry_sector);

-- Add index on hq_country (used in location filtering)
CREATE INDEX IF NOT EXISTS idx_hq_country ON companies(hq_country);

-- Verify indexes were created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'companies'
ORDER BY indexname;
