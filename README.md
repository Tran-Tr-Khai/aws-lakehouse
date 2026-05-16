# NYC Taxi Azure Databricks Batch Lakehouse

## Overview

This project builds a batch lakehouse pipeline for NYC Yellow Taxi trip records using Azure Databricks, ADLS Gen2, PySpark, and Delta Lake.

The goal is to process monthly taxi trip parquet files from raw landing storage into Bronze, Silver, and Gold Delta tables for analytics and dashboarding.

## Business Questions

The project answers the following questions:

1. When does taxi demand peak by hour and day?
2. Which pickup zones generate the most revenue?
3. Which pickup-to-dropoff routes are the most profitable?
4. How does payment type affect tipping behavior?
5. Which trips look anomalous or invalid?

## Architecture

