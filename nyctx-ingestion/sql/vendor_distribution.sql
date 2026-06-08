SELECT VendorID, COUNT(*) AS total_rows 
FROM read_parquet('{trip_file_sql}') 
GROUP BY VendorID ORDER BY VendorID;