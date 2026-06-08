SELECT RatecodeID, COUNT(*) AS total_rows 
FROM read_parquet('{trip_file_sql}') 
GROUP BY RatecodeID ORDER BY RatecodeID;