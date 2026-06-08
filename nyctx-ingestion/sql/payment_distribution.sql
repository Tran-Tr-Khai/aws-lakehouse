SELECT payment_type, COUNT(*) AS total_rows 
FROM read_parquet('{trip_file_sql}') 
GROUP BY payment_type ORDER BY payment_type;