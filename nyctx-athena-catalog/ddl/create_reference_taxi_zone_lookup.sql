CREATE EXTERNAL TABLE IF NOT EXISTS __NYCTX_ATHENA_DATABASE__.reference_taxi_zone_lookup (
    locationid STRING,
    borough STRING,
    zone STRING,
    service_zone STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"',
    'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION '__NYCTX_ZONE_LOOKUP_LOCATION__'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);
