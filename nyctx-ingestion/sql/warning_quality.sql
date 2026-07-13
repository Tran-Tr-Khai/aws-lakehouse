SELECT
    COUNT(*) FILTER (
        WHERE (VendorID IS NOT NULL AND VendorID NOT IN (1, 2))
           OR (payment_type IS NOT NULL AND payment_type NOT IN (1, 2, 3, 4, 5, 6))
           OR (RatecodeID IS NOT NULL AND RatecodeID NOT IN (1, 2, 3, 4, 5, 6, 99))
           OR (store_and_fwd_flag IS NOT NULL AND store_and_fwd_flag NOT IN ('Y', 'N'))
           OR extra < 0
           OR mta_tax < 0
           OR tip_amount < 0
           OR tolls_amount < 0
           OR improvement_surcharge < 0
           OR congestion_surcharge < 0
           OR Airport_fee < 0
           OR (PULocationID IS NOT NULL AND (PULocationID < 1 OR PULocationID > 265))
           OR (DOLocationID IS NOT NULL AND (DOLocationID < 1 OR DOLocationID > 265))
           OR trip_distance > 100
           OR date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440
    ) AS warning_row_count,
    COUNT(*) FILTER (WHERE VendorID IS NOT NULL AND VendorID NOT IN (1, 2))
        AS invalid_vendor_count,
    COUNT(*) FILTER (
        WHERE payment_type IS NOT NULL AND payment_type NOT IN (1, 2, 3, 4, 5, 6)
    ) AS invalid_payment_type_domain_count,
    COUNT(*) FILTER (
        WHERE RatecodeID IS NOT NULL AND RatecodeID NOT IN (1, 2, 3, 4, 5, 6, 99)
    ) AS invalid_ratecode_count,
    COUNT(*) FILTER (
        WHERE store_and_fwd_flag IS NOT NULL AND store_and_fwd_flag NOT IN ('Y', 'N')
    ) AS invalid_store_and_fwd_flag_count,
    COUNT(*) FILTER (WHERE extra < 0) AS negative_extra_count,
    COUNT(*) FILTER (WHERE mta_tax < 0) AS negative_mta_tax_count,
    COUNT(*) FILTER (WHERE tip_amount < 0) AS negative_tip_count,
    COUNT(*) FILTER (WHERE tolls_amount < 0) AS negative_tolls_count,
    COUNT(*) FILTER (WHERE improvement_surcharge < 0)
        AS negative_improvement_surcharge_count,
    COUNT(*) FILTER (WHERE congestion_surcharge < 0)
        AS negative_congestion_surcharge_count,
    COUNT(*) FILTER (WHERE Airport_fee < 0) AS negative_airport_fee_count,
    COUNT(*) FILTER (
        WHERE PULocationID IS NOT NULL AND (PULocationID < 1 OR PULocationID > 265)
    ) AS pickup_location_out_of_range_count,
    COUNT(*) FILTER (
        WHERE DOLocationID IS NOT NULL AND (DOLocationID < 1 OR DOLocationID > 265)
    ) AS dropoff_location_out_of_range_count,
    COUNT(*) FILTER (WHERE trip_distance > 100) AS very_long_distance_count,
    COUNT(*) FILTER (
        WHERE date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440
    ) AS very_long_duration_count
FROM read_parquet('{trip_file_sql}');
