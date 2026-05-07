-- ==============================================================================
-- query.sql — Base Issue Volume Query
-- ==============================================================================
-- One base query.  DataService aggregates it in-memory per detection level.
-- ==============================================================================

-- @query base
SELECT
    ISSUE_RECEIVED AS DT,
    CLIENT_NAME,
    ISSUE_CATEGORY,
    ISSUE_SUBCATEGORY,
    COUNT(DISTINCT NUMBER) AS ISSUE_VOLUME
FROM CDW_PRD_CALL_DB.CDW_COVE_RPT_SC.ISSUE_BASE_DETAIL_FACT_TABLE
WHERE source_system = 'OptumRxServiceNow'
GROUP BY ALL
;
