SELECT store_and_fwd_flag, COUNT(*) AS total_rows
FROM read_parquet('{trip_file_sql}')
GROUP BY store_and_fwd_flag ORDER BY store_and_fwd_flag;