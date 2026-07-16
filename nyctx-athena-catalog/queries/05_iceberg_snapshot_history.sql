SELECT
    committed_at,
    snapshot_id,
    parent_id,
    operation,
    manifest_list
FROM __NYCTX_ATHENA_DATABASE__."__NYCTX_ATHENA_ICEBERG_TABLE__$snapshots"
ORDER BY committed_at DESC
LIMIT 20;