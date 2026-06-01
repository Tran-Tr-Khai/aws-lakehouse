# nyctx-bi-dashboard

Power BI reports and dashboard assets for the NYC Taxi Lakehouse.

## Structure

```
powerbi/        # Power BI .pbix report files
screenshots/    # Dashboard screenshots for documentation
```

> Connects to AWS Athena Gold layer tables via ODBC/DirectQuery.

## Market Hotspots Map

Use explicit coordinates from the Gold `dim_zone` table instead of Power BI
auto-geocoding taxi zone names:

```text
Latitude   -> dim_zone[latitude]
Longitude  -> dim_zone[longitude]
Size       -> trips or revenue measure from mart_pickup_zone_performance
Legend     -> dim_zone[borough]
Tooltip    -> zone, borough, trips, revenue, avg trip amount
```

Recommended model relationship:

```text
dim_zone[location_id] 1 -> * mart_pickup_zone_performance[pickup_location_id]
```

This makes the Page 3 map stable across refreshes and avoids incorrect matches
for neighborhood names that exist outside NYC.
