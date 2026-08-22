---
layout: post
title: "HyperLogLog: How Google and Reddit Count Billions of Unique Users Using Just 12 KB"
description: "A simple, intuitive explanation of the HyperLogLog algorithm — how it works, why it is used over sets and bloom filters, and when you should (and shouldn't) use it."
date: 2026-08-22
categories:
  - DataStructures
  - Backend
tags:
  - hyperloglog
  - redis
  - algorithms
  - cardinality
  - probabilistic-data-structures
  - system-design
author: "Saiteja Chada"
reading_time: "8 min read"
draft: false
---

If you run a service at scale and want to calculate Daily Active Users (DAU) or unique page visits, the most intuitive approach is to collect user identifiers in a Hash Set or Redis Set. Sets automatically deduplicate items, making `set.size()` or `SCARD` an obvious solution.

However, memory scaling quickly becomes a bottleneck.

If you have 1 billion unique users in a single day and store each 64-bit ID (8 bytes), raw ID storage alone requires:

```text
1,000,000,000 * 8 bytes ≈ 8 GB
```

With hash table pointer overhead, memory fragmentation, and key storage, this easily exceeds 15–20 GB of RAM for a single metric. If you want to track uniques across different dimensions (such as per-page, per-country, or per-hour), maintaining exact sets in memory becomes impractical.

---

## Why Not Bloom Filters?

A common follow-up thought is using a **Bloom Filter**. While Bloom Filters are space-efficient probabilistic data structures, they are designed for set membership checks: *"Is user X in this set?"*

They do not maintain a cardinality count. To estimate set size from a Bloom Filter, you have to compute it indirectly from bit density, which degrades in accuracy as the filter fills up and still requires substantial memory (often megabytes to gigabytes for billion-scale sets).

---

## The HyperLogLog Approach

**HyperLogLog (HLL)** is a probabilistic cardinality estimation algorithm introduced by Philippe Flajolet et al. in 2007. Instead of storing actual element values, it tracks statistical properties of hashed inputs to estimate cardinality with a standard error of roughly **0.81%**, using a constant **12 KB of memory** regardless of whether you process 10,000 or 10 billion items.

Because it is probabilistic, it is not suitable for financial transactions or billing systems where exact counts are mandatory. But for metrics, telemetry, and analytics, an error margin under 1% is usually an acceptable engineering trade-off for orders-of-magnitude memory savings.

---

## Core Mechanism

The algorithm relies on the uniform distribution of hash outputs and the probability of consecutive leading zeros.

### 1. Uniform Hashing
When an element (such as a user ID string or UUID) is added, it is passed through a 64-bit hash function (like MurmurHash64 or xxHash). The output is a uniformly distributed 64-bit binary sequence where each bit has an independent 50% probability of being `0` or `1`.

```text
Input: "user_98412" -> 00000101011010101101010101110101...
```

### 2. Observing Leading Zeros
In a random stream of binary numbers:
- Probability of starting with `0`: 1/2 ($2^{-1}$)
- Probability of starting with `00`: 1/4 ($2^{-2}$)
- Probability of starting with `00000` (5 zeros): 1/32 ($2^{-5}$)
- Probability of $k$ leading zeros: $1/2^k$

If you observe an output with $k$ leading zeros before the first `1`, it implies that statistically around $2^k$ items have been processed.

### 3. Splitting into Registers (Bucketing)
Relying on a single maximum count of leading zeros has high variance. A single outlier hash starting with 25 zeros would immediately skew the estimate to 33 million.

To reduce variance, HyperLogLog partitions the dataset across $m = 2^p$ registers:
- The first $p$ bits of the 64-bit hash select the register index.
- The remaining $64 - p$ bits are evaluated for the count of leading zeros plus one ($\rho$).
- The target register only updates if the new leading zero count is greater than its current value.

For example, with $p = 4$ ($2^4 = 16$ registers):

```text
Hash: [ 0000 ] [ 0101010101010101... ]
        |              |
     First 4 bits   Remaining 60 bits
     Register 0     Starts with "01" -> 1 leading zero
```

Register `0` records $\max(\text{existing}, 1 + 1)$.

### 4. Harmonic Mean & Bias Correction
To calculate the overall estimate from all registers $M[0 \dots m-1]$, HyperLogLog computes the harmonic mean across the register values:

$$E = \alpha_m \cdot m^2 \cdot \left( \sum_{j=1}^{m} 2^{-M[j]} \right)^{-1}$$

The harmonic mean heavily dampens the impact of extreme outliers compared to an arithmetic mean. The constant $\alpha_m$ provides bias correction for register sizing.

---

## Memory Comparison

| Structure | Storage Method | Memory for 1B Items | Precision |
|---|---|---|---|
| Hash Set | Stores raw IDs | ~8–16 GB | Exact (100%) |
| Bloom Filter | Bit array (membership) | ~1.2 GB (at 1% FPR) | Approximate membership only |
| HyperLogLog | 16,384 6-bit registers | ~12 KB | Approximate (~0.81% error) |

Redis uses $p = 14$, allocating $2^{14} = 16,384$ registers. Since the maximum leading zero count in a 64-bit hash fits in 6 bits ($2^6 = 64$), each register is 6 bits wide:

$$16,384 \times 6 \text{ bits} = 98,304 \text{ bits} = 12 \text{ KB}$$

---

## Redis Implementation

Redis provides native support for HyperLogLog using three primary commands:

```bash
# Add elements
PFADD unique_visitors:2026-08-22 "user_101" "user_102" "user_103"

# Retrieve estimated cardinality
PFCOUNT unique_visitors:2026-08-22
# Output: 3

# Merge multiple HyperLogLogs without recounting raw records
PFMERGE monthly_visitors:2026-08 unique_visitors:2026-08-01 unique_visitors:2026-08-02
PFCOUNT monthly_visitors:2026-08
```

The command prefix `PF` honors Philippe Flajolet.

---

## Trade-offs and Practical Suitability

### When to Use HyperLogLog
- High-volume cardinality estimation (DAU, MAU, unique IP monitoring, search query frequency).
- Systems where storing identifiers in memory is cost-prohibitive.
- Distributed data pipelines where pre-aggregating and merging sketches (`PFMERGE`) avoids shuffling raw IDs over the network.

### When Not to Use HyperLogLog
- Auditing, financial ledgers, or invoice billing requiring exact counts.
- Workflows that need to retrieve, inspect, or iterate over the actual elements.
- Membership verification (use a Bloom Filter or Cuckoo Filter instead).
- Datasets with very low cardinality where standard sets fit easily in memory without approximation.

---

## Real-World Systems

- **Google BigQuery:** Exposes HyperLogLog through `APPROX_COUNT_DISTINCT()`, drastically reducing query latency and memory consumption over massive datasets compared to `COUNT(DISTINCT)`.
- **Redis:** Used as a lightweight analytics cache layer for real-time dashboards.
- **Apache Spark / Trino / Presto:** Use HLL sketches for distributed distinct counting across petabyte-scale tables.
- **Cloudflare:** Applies HyperLogLog sketches for real-time edge DDoS tracking and unique visitor analytics.

---

## References
1. Flajolet, P., Fusy, É., Gandouet, O., & Meunier, F. (2007). *HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm*. Discrete Mathematics and Theoretical Computer Science.
2. Heule, S., Nunkesser, M., & Hall, A. (2013). *HyperLogLog in Practice: Algorithmic Engineering of a State of The Art Cardinality Estimation Algorithm* (Google Engineering).
3. Redis Documentation: [Probabilistic data structures - HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/).
