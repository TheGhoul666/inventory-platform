---
name: data-pipeline
description: Use when building ETL pipelines, data ingestion, data transformation, Airflow DAGs, dbt models, streaming data processing, or orchestrating data workflows.
---

You are a **Data Pipeline Engineer** — you build reliable, scalable data pipelines that move and transform data.

## Python ETL Pipeline

```python
import pandas as pd
from dataclasses import dataclass
from typing import Generator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    source_db_url: str
    dest_db_url: str
    batch_size: int = 1000
    start_date: datetime = None

class ETLPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stats = {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0}
    
    def extract(self) -> Generator[pd.DataFrame, None, None]:
        """Extract in batches to avoid memory issues"""
        query = """
            SELECT * FROM orders
            WHERE created_at > %(start_date)s
            ORDER BY created_at
        """
        with psycopg2.connect(self.config.source_db_url) as conn:
            for chunk in pd.read_sql(
                query, conn, 
                params={'start_date': self.config.start_date},
                chunksize=self.config.batch_size
            ):
                self.stats['extracted'] += len(chunk)
                yield chunk
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and enrich data"""
        # Type conversions
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Derived fields
        df['revenue_usd'] = df['amount'] / df['exchange_rate']
        df['is_high_value'] = df['revenue_usd'] > 1000
        df['day_of_week'] = df['created_at'].dt.day_name()
        
        # Deduplication
        df = df.drop_duplicates(subset=['order_id'])
        
        # Drop nulls in required fields
        required = ['order_id', 'user_id', 'amount']
        null_mask = df[required].isnull().any(axis=1)
        if null_mask.any():
            logger.warning(f"Dropping {null_mask.sum()} rows with null required fields")
            df = df[~null_mask]
        
        self.stats['transformed'] += len(df)
        return df
    
    def load(self, df: pd.DataFrame) -> None:
        """Upsert to destination"""
        with psycopg2.connect(self.config.dest_db_url) as conn:
            buffer = io.StringIO()
            df.to_csv(buffer, index=False, header=False)
            buffer.seek(0)
            
            with conn.cursor() as cur:
                # Create temp table
                cur.execute("CREATE TEMP TABLE staging (LIKE orders INCLUDING ALL)")
                cur.copy_from(buffer, 'staging', sep=',', null='')
                
                # Upsert
                cur.execute("""
                    INSERT INTO orders SELECT * FROM staging
                    ON CONFLICT (order_id) DO UPDATE
                    SET revenue_usd = EXCLUDED.revenue_usd,
                        updated_at = NOW()
                """)
                
                conn.commit()
        
        self.stats['loaded'] += len(df)
    
    def run(self) -> dict:
        logger.info("Pipeline started")
        start_time = datetime.now()
        
        for batch in self.extract():
            try:
                transformed = self.transform(batch)
                self.load(transformed)
            except Exception as e:
                self.stats['errors'] += len(batch)
                logger.error(f"Batch failed: {e}")
        
        self.stats['duration_seconds'] = (datetime.now() - start_time).seconds
        logger.info(f"Pipeline completed: {self.stats}")
        return self.stats
```

## Airflow DAG

```python
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

@dag(
    schedule='0 2 * * *',  # 2am daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args={
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'on_failure_callback': notify_slack_on_failure,
    },
    tags=['etl', 'orders'],
)
def orders_daily_etl():
    
    @task
    def extract_orders(logical_date: datetime = None) -> list[dict]:
        hook = PostgresHook(postgres_conn_id='source_db')
        sql = "SELECT * FROM orders WHERE DATE(created_at) = %(date)s"
        rows = hook.get_records(sql, parameters={'date': logical_date.date()})
        return [dict(zip([col for col in hook.get_first(f"SELECT column_name FROM information_schema.columns WHERE table_name='orders'")], row)) for row in rows]
    
    @task
    def transform_orders(raw_orders: list[dict]) -> list[dict]:
        df = pd.DataFrame(raw_orders)
        df = clean_and_enrich(df)
        return df.to_dict('records')
    
    @task
    def load_orders(orders: list[dict]) -> None:
        hook = PostgresHook(postgres_conn_id='dest_db')
        hook.insert_rows('orders_mart', orders, replace=True, replace_index=['order_id'])
    
    @task
    def run_data_quality_checks(orders: list[dict]) -> None:
        df = pd.DataFrame(orders)
        assert df['order_id'].is_unique, "Duplicate order IDs found"
        assert df['amount'].ge(0).all(), "Negative amounts found"
        assert df['user_id'].notna().all(), "Missing user IDs"
    
    # DAG flow
    raw = extract_orders()
    cleaned = transform_orders(raw)
    run_data_quality_checks(cleaned)
    load_orders(cleaned)

orders_daily_etl()
```

## dbt Models

```sql
-- models/staging/stg_orders.sql
{{ config(materialized='view') }}

SELECT
    order_id,
    user_id,
    CAST(created_at AS TIMESTAMP WITH TIME ZONE) AS created_at,
    CAST(amount AS DECIMAL(10,2)) AS amount,
    LOWER(TRIM(status)) AS status,
    currency
FROM {{ source('raw', 'orders') }}
WHERE order_id IS NOT NULL

-- models/marts/fct_orders.sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='sync_all_columns'
) }}

SELECT
    o.order_id,
    o.user_id,
    u.email,
    u.country,
    o.created_at,
    o.amount,
    o.amount * er.rate AS amount_usd,
    o.status,
    DATE_TRUNC('week', o.created_at) AS week,
    DATE_TRUNC('month', o.created_at) AS month
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('dim_users') }} u ON u.user_id = o.user_id
LEFT JOIN {{ ref('exchange_rates') }} er 
    ON er.currency = o.currency AND er.date = o.created_at::DATE

{% if is_incremental() %}
WHERE o.created_at > (SELECT MAX(created_at) FROM {{ this }})
{% endif %}
```

## Streaming (Kafka → PostgreSQL)

```python
from confluent_kafka import Consumer
import json

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'orders-consumer',
    'auto.offset.reset': 'latest',
    'enable.auto.commit': False,  # Manual commit for exactly-once
})
consumer.subscribe(['orders'])

buffer = []
BATCH_SIZE = 100

while True:
    msg = consumer.poll(timeout=1.0)
    
    if msg is None:
        if buffer:  # Flush on timeout
            load_batch(buffer)
            consumer.commit()
            buffer.clear()
        continue
    
    if msg.error():
        logger.error(f"Consumer error: {msg.error()}")
        continue
    
    order = json.loads(msg.value())
    buffer.append(order)
    
    if len(buffer) >= BATCH_SIZE:
        load_batch(buffer)
        consumer.commit()
        buffer.clear()
```
