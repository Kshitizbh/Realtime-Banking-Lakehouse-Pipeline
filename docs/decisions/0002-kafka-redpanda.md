# 0002 - Streaming broker: Redpanda instead of Apache Kafka

- Status: accepted
- Date: 2026-11-20

## Context
The capstone brief lists Kafka as a required technology for streaming transaction
events and the DLQ topic. The whole platform runs on one laptop (WSL capped at 16 GB)
alongside Spark, Trino, Airflow, Postgres and the object store, and earlier attempts
at this kind of stack crashed the laptop because of memory pressure.

## Options considered
| Option | For | Against |
|---|---|---|
| Apache Kafka (KRaft mode) | Exactly what the brief names | JVM-based, heavier to run next to Spark, Trino and Airflow on one laptop |
| **Redpanda** | Speaks the Kafka API, single binary, no ZooKeeper or JVM, built-in console UI | Not literally "Kafka"; licensed as source-available rather than Apache 2.0 |
| Managed cloud Kafka | No local resources | Costs money, needs internet, not "local" as the brief requires |

## Decision
Use Redpanda as the broker, and treat it strictly as a Kafka-compatible endpoint.

## Consequences
- Producers use the standard Kafka client (`confluent-kafka`) and Spark uses its standard
  Kafka source and sink, so all code and skills are Kafka skills.
- No Redpanda-specific features are used. Switching to Apache Kafka means changing the
  broker service in `docker-compose.yml` only; no application code changes.
- Topics follow the brief: `banking.transactions.raw`, `banking.transactions.validated`,
  `banking.transactions.dlq`, `banking.fraud.alerts`.
- This is a deviation from the brief and must be explained in the final presentation.
