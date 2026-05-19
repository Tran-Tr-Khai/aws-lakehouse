# NYC Taxi AWS Lakehouse Pipeline

## Overview

This project builds a batch lakehouse pipeline for NYC Yellow Taxi trip records using AWS S3, AWS Glue Data Catalog, Athena, Python, and Parquet.

The goal is to process monthly taxi trip parquet files from raw Bronze storage into cleaned Silver datasets and Gold analytics marts for SQL analytics and dashboarding.

## Business Questions

The project answers the following questions:

1. When does taxi demand peak by hour and day?
2. Which pickup zones generate the most revenue?
3. Which pickup-to-dropoff routes are the most profitable?
4. How does payment type affect tipping behavior?
5. Which trips look anomalous or invalid?

## Architecture

