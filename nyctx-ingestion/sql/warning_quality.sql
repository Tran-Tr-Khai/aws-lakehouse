SELECT
    SUM(CASE WHEN VendorID IS NOT NULL AND VendorID NOT IN (1, 2) THEN 1 ELSE 0 END) AS invalid_vendor_count,
    SUM(CASE WHEN payment_type IS NOT NULL AND payment_type NOT IN (1, 2, 3, 4, 5, 6) THEN 1 ELSE 0 END) AS invalid_payment_type_domain_count,
    SUM(CASE WHEN RatecodeID IS NOT NULL AND RatecodeID NOT IN (1, 2, 3, 4, 5, 6, 99) THEN 1 ELSE 0 END) AS invalid_ratecode_count,
    SUM(CASE WHEN store_and_fwd_flag IS NOT NULL AND store_and_fwd_flag NOT IN ('Y', 'N') THEN 1 ELSE 0 END) AS invalid_store_and_fwd_flag_count,
    SUM(CASE WHEN extra < 0 THEN 1 ELSE 0 END) AS negative_extra_count,
    SUM(CASE WHEN mta_tax < 0 THEN 1 ELSE 0 END) AS negative_mta_tax_count,
    SUM(CASE WHEN tip_amount < 0 THEN 1 ELSE 0 END) AS negative_tip_count,
    SUM(CASE WHEN tolls_amount < 0 THEN 1 ELSE 0 END) AS negative_tolls_count,
    SUM(CASE WHEN improvement_surcharge < 0 THEN 1 ELSE 0 END) AS negative_improvement_surcharge_count,
    SUM(CASE WHEN congestion_surcharge < 0 THEN 1 ELSE 0 END) AS negative_congestion_surcharge_count,
    SUM(CASE WHEN Airport_fee < 0 THEN 1 ELSE 0 END) AS negative_airport_fee_count,
    SUM(CASE WHEN PULocationID IS NOT NULL AND (PULocationID < 1 OR PULocationID > 265) THEN 1 ELSE 0 END) AS pickup_location_out_of_range_count,
    SUM(CASE WHEN DOLocationID IS NOT NULL AND (DOLocationID < 1 OR DOLocationID > 265) THEN 1 ELSE 0 END) AS dropoff_location_out_of_range_count,
    SUM(CASE WHEN trip_distance > 100 THEN 1 ELSE 0 END) AS very_long_distance_count,
    SUM(CASE WHEN date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440 THEN 1 ELSE 0 END) AS very_long_duration_count
FROM read_parquet('{trip_file_sql}');