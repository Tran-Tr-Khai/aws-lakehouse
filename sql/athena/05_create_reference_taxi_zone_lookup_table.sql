CREATE EXTERNAL TABLE IF NOT EXISTS nyc_taxi_lakehouse.reference_taxi_zone_lookup (
    LocationID INT,
    Borough STRING,
    Zone STRING,
    service_zone STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION 's3://nyc-taxi-lakehouse-tntk/reference/'
TBLPROPERTIES (
    "skip.header.line.count" = "1"
);