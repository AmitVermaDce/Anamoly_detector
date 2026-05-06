-- =============================================================================
-- issue_volume.sql — All Issue Volume Queries
-- =============================================================================
-- Queries are delimited by  -- @query <key>  markers.
-- The snowflake_service reads this file and extracts queries by key.
-- =============================================================================


-- @query by_client
SELECT
    ISSUE_RECEIVED AS DT,
    CLIENT_NAME,
    COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL
;


-- @query by_category
SELECT
    ISSUE_RECEIVED AS DT,
    ISSUE_CATEGORY,
    COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL
;


-- @query by_subcategory
SELECT
    ISSUE_RECEIVED AS DT,
    ISSUE_SUBCATEGORY,
    COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL
;


-- @query by_client_category
SELECT
    ISSUE_RECEIVED AS DT,
    CLIENT_NAME,
    ISSUE_CATEGORY,
    COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL
;
