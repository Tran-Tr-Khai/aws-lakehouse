from pathlib import Path


EXPECTED_SILVER_SCHEMA = [
    ('vendor_id', 'INT'),
    ('pickup_datetime', 'TIMESTAMP'),
    ('dropoff_datetime', 'TIMESTAMP'),
    ('passenger_count', 'BIGINT'),
    ('trip_distance', 'DOUBLE'),
    ('ratecode_id', 'BIGINT'),
    ('store_and_fwd_flag', 'STRING'),
    ('pickup_location_id', 'INT'),
    ('dropoff_location_id', 'INT'),
    ('payment_type', 'BIGINT'),
    ('fare_amount', 'DOUBLE'),
    ('extra', 'DOUBLE'),
    ('mta_tax', 'DOUBLE'),
    ('tip_amount', 'DOUBLE'),
    ('tolls_amount', 'DOUBLE'),
    ('improvement_surcharge', 'DOUBLE'),
    ('total_amount', 'DOUBLE'),
    ('congestion_surcharge', 'DOUBLE'),
    ('airport_fee', 'DOUBLE'),
    ('trip_duration_minutes', 'DOUBLE'),
    ('pickup_date', 'DATE'),
    ('pickup_hour', 'INT'),
    ('pickup_day_of_week', 'STRING'),
    ('fare_per_mile', 'DOUBLE'),
    ('tip_rate', 'DOUBLE'),
    ('avg_speed_mph', 'DOUBLE'),
    ('fare_per_minute', 'DOUBLE'),
    ('same_pickup_dropoff_zone', 'BOOLEAN'),
    ('is_invalid_vendor', 'BOOLEAN'),
    ('is_invalid_payment_type_domain', 'BOOLEAN'),
    ('is_invalid_ratecode', 'BOOLEAN'),
    ('is_invalid_store_and_fwd_flag', 'BOOLEAN'),
    ('has_negative_fee_component', 'BOOLEAN'),
    ('is_pickup_location_out_of_range', 'BOOLEAN'),
    ('is_dropoff_location_out_of_range', 'BOOLEAN'),
    ('is_very_long_distance', 'BOOLEAN'),
    ('is_very_long_duration', 'BOOLEAN'),
    ('has_warning_quality_issue', 'BOOLEAN'),
    ('is_extreme_speed', 'BOOLEAN'),
    ('is_fare_distance_mismatch', 'BOOLEAN'),
    ('is_distance_duration_mismatch', 'BOOLEAN'),
    ('is_same_zone_high_fare', 'BOOLEAN'),
    ('is_analytical_outlier', 'BOOLEAN'),
    ('year', 'STRING'),
    ('month', 'STRING'),
]


def test_silver_ddl_matches_output_schema_contract() -> None:
    ddl_path = (
        Path(__file__).resolve().parents[1]
        / 'ddl'
        / 'create_silver_yellow_taxi_iceberg.sql'
    )
    ddl = ddl_path.read_text(encoding='utf-8')
    columns_block = ddl.split('(', 1)[1].split(')\nPARTITIONED BY', 1)[0]
    actual_schema = [
        tuple(line.strip().rstrip(',').split())
        for line in columns_block.splitlines()
        if line.strip()
    ]

    assert actual_schema == EXPECTED_SILVER_SCHEMA
