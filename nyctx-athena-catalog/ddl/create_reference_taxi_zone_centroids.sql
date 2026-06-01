CREATE EXTERNAL TABLE IF NOT EXISTS __NYCTX_ATHENA_DATABASE__.reference_taxi_zone_centroids (
    location_id STRING,
    latitude STRING,
    longitude STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"',
    'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION '__NYCTX_ZONE_CENTROIDS_LOCATION__'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);
