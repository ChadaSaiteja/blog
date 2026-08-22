---
layout: post
title: "HyperLogLog: How Google and Redis Count Billions of Unique Users Using Just 12 KB"
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

Imagine you are running a website like YouTube or Google Search. Every single day, hundreds of millions of people visit your platform. At the end of the day, your product team asks: **"How many unique users visited today?"**

Simple question. But the answer involves some seriously clever engineering.

---

## The Obvious Approach (And Why It Breaks)

The first instinct is straightforward: whenever a new user visits, store their user ID somewhere. At the end of the day, count the entries. You could use a data structure like a **Hash Set** or a **Sorted Set** — both are great for this because they naturally deduplicate entries (the same user ID won't be counted twice).

This works perfectly… until it doesn't.

Let's say you have **1 billion unique users**. If each user ID is a 64-bit integer (8 bytes), you need:

```
1,000,000,000 users × 8 bytes = ~8 GB of memory
```

Just to count unique visitors. Every day. And that's before you factor in metadata, indexes, or any other overhead. For a company with billions of users across dozens of products, this becomes completely unmanageable.

---

## What About a Bloom Filter?

You might have heard of **Bloom Filters** — another probabilistic data structure that trades accuracy for memory efficiency. A Bloom Filter can tell you with high confidence whether an element is *probably* in the set or *definitely not* in the set.

But here's the catch: a Bloom Filter is great for answering **"Have I seen this user before?"** — it cannot directly tell you **"How many unique users have I seen?"**. You still need to maintain a counter alongside it. And at massive scale, Bloom Filters still consume significant memory.

There had to be a better way.

---

## Enter HyperLogLog

**HyperLogLog** (HLL) is a probabilistic algorithm designed specifically to solve the **cardinality estimation** problem — i.e., counting unique elements in a large dataset. It was introduced by Philippe Flajolet and colleagues in 2007.

The key idea: instead of storing every user ID, HyperLogLog only stores a **tiny summary** of what it has seen, and uses probability to estimate the count.

> **The trade-off:** HyperLogLog gives you an *approximate* answer, not an exact one. The error rate is typically around **±0.81%**. If you absolutely need the exact count (for billing, legal, or compliance reasons), HyperLogLog is not for you. But for analytics — daily active users, unique page views, unique search queries — this margin is completely acceptable.

Redis's HyperLogLog uses a fixed **12 KB of memory**, regardless of whether you are counting 1,000 or 1 billion unique users.

---

## How Does It Actually Work?

Let me walk you through the intuition step by step.

### Step 1: The Coin Flip Intuition

Imagine you are flipping a fair coin repeatedly and noting how long your streak of heads is before you get a tail. If I tell you the longest streak you observed was **3 heads in a row**, you probably didn't flip the coin that many times. But if I tell you the longest streak was **20 heads in a row**, you almost certainly flipped it millions of times — because the probability of getting 20 heads in a row is 1 in 2²⁰ (about 1 in a million).

This is the core intuition behind HyperLogLog.

### Step 2: Hashing Everything

When a user ID comes in, HyperLogLog first passes it through a **hash function** (like MurmurHash or xxHash). This is critical because:

- Hash functions produce uniformly distributed output
- Every input maps to a random-looking 64-bit binary string
- This turns any kind of user ID (strings, integers, UUIDs) into a series of random bits

For example, a user ID `"user_12345"` might hash to:

```
0000010101101010110101010111010101010101010101010101010101010101
```

### Step 3: Counting Leading Zeros

Now, look at the hash value. Count how many **leading zeros** appear before the first `1`.

In the example above: `00000` → 5 leading zeros.

Here is the probabilistic magic:

- The probability of getting **1 leading zero** is 1/2
- The probability of getting **2 leading zeros** is 1/4
- The probability of getting **n leading zeros** is 1/2ⁿ

So if the maximum number of leading zeros you've ever seen across all hashed user IDs is **n**, then statistically you've probably seen around **2ⁿ** unique users.

### Step 4: Registers (Dividing to Reduce Error)

There's a problem with just tracking one maximum value — a single outlier (one unlucky hash with 30 leading zeros) would completely blow up your estimate.

The solution is to **split the work into many independent sub-experiments** called **registers** (or buckets). This is controlled by a parameter **p**:

- The **first p bits** of the hash value determine *which register* this element belongs to
- The **remaining bits** are used to count the leading zeros, stored in that register

If `p = 4`, you get `2⁴ = 16` registers. Each register independently tracks the maximum leading zeros it has seen.

**Example with p = 4:**

```
Hash: 0000 | 010101010101010101010101010101010101010101010101010101010101
       ↑              ↑
  first 4 bits    remaining 60 bits → count leading zeros here
  = "0000"        starts with "0" → 1 leading zero
  → register index 0
```

Each register stores a small number — just the maximum leading zeros seen so far for its slice of the data.

### Step 5: Combining with the Harmonic Mean

Once all user IDs are processed, you combine all the register values using the **harmonic mean** (not a simple average — the harmonic mean reduces the impact of outliers), apply a correction factor **αₘ**, and get your final estimate:

```
Estimated Cardinality = αₘ × m² × HarmonicMean(2^(-register[i]))
```

Where `m` is the number of registers. The correction factor `αₘ` compensates for known biases in the estimation at very low or very high counts.

---

## Memory: The Real Win

Here's the numbers that make HyperLogLog remarkable:

| Approach | 1 Billion Users | Memory Used |
|---|---|---|
| Hash Set (exact) | 1,000,000,000 IDs stored | ~8 GB |
| Bloom Filter | Bit array for 1B items | ~1.2 GB (with 1% error) |
| **HyperLogLog** | **16K registers, each a few bits** | **~12 KB** |

Redis specifically uses `p = 14`, which gives `2¹⁴ = 16,384` registers. Each register stores at most 6 bits. Total: `16,384 × 6 bits ≈ 12 KB`.

That is a **~700,000x reduction** in memory compared to storing every ID — with only a 0.81% error rate.

---

## How Redis Exposes This

Redis makes HyperLogLog a first-class citizen with three commands:

```bash
# Add elements to the HyperLogLog
PFADD daily_visitors:2026-08-22 user_001 user_002 user_003

# Get the estimated unique count
PFCOUNT daily_visitors:2026-08-22
# → (integer) 3

# Merge multiple HLLs (e.g., get monthly uniques from daily HLLs)
PFMERGE monthly_visitors:2026-08 daily_visitors:2026-08-01 daily_visitors:2026-08-02
PFCOUNT monthly_visitors:2026-08
```

The `PF` prefix is a tribute to **Philippe Flajolet**, the algorithm's inventor.

---

## A Quick Comparison

| Feature | Hash Set | Bloom Filter | HyperLogLog |
|---|---|---|---|
| **Memory** | O(n) — grows with data | O(n) — large but fixed | O(1) — always ~12 KB |
| **Exact count?** | ✅ Yes | ❌ No | ❌ No (~0.81% error) |
| **Can list elements?** | ✅ Yes | ❌ No | ❌ No |
| **Membership check?** | ✅ Yes | ✅ Yes (probabilistic) | ❌ No |
| **Cardinality estimation** | ✅ Exact | ❌ Indirect | ✅ Approximate |
| **Best for** | Small-medium exact data | "Have I seen this?" | Counting unique at scale |

---

## When to Use HyperLogLog (and When Not To)

### ✅ Use HyperLogLog when:
- You need to count **unique users, events, searches, or IPs** at scale
- An approximate answer with **~1% error** is acceptable
- Memory is a constraint and your dataset is massive
- You are building analytics dashboards, monitoring systems, or real-time metrics

### ❌ Avoid HyperLogLog when:
- You need the **exact** count — for billing, compliance, or financial transactions
- You need to **retrieve or iterate** over the actual unique elements
- Your dataset is small — a plain Redis Set is fine for a few thousand items
- You need to check **membership** (whether a specific user is in the set)

---

## Real-World Usage

- **Google** uses variants of HyperLogLog internally for counting unique search queries and unique users per product. BigQuery's `APPROX_COUNT_DISTINCT` function is backed by HLL under the hood.
- **Redis** ships HyperLogLog as a built-in data type, widely used by companies for real-time unique counting in analytics pipelines.
- **Apache Spark, Presto, and Flink** all support HLL-based approximate distinct counts for large-scale data processing.
- **Cloudflare** uses HyperLogLog for estimating unique IP addresses in network traffic analysis.

---

## The Bottom Line

HyperLogLog is one of those algorithms where the cleverness is almost poetic. By exploiting the statistics of random bit patterns — something as simple as counting leading zeros — it can tell you "you probably have 1 billion unique users" using less memory than a single high-resolution image.

The key things to remember:

1. **It gives an approximation**, not an exact answer (~0.81% error with Redis's default settings)
2. **Memory is constant** — 12 KB whether you have 1 user or 1 billion
3. **You cannot retrieve the items** — only get the estimated count
4. **Use it for analytics** where "approximately 5 million unique users" is a perfectly useful answer
5. **Avoid it for billing or compliance** where you need the exact number

The next time you see "5.2M unique visitors this month" on an analytics dashboard, there's a good chance HyperLogLog is doing the counting behind the scenes.

---

## References
1. [HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm](http://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf) — Philippe Flajolet et al. (2007)
2. [Redis HyperLogLog documentation](https://redis.io/docs/data-types/probabilistic/hyperloglogs/)
3. [HyperLogLog in Practice — Google Engineering](https://research.google/pubs/hyperloglog-in-practice-algorithmic-engineering-of-a-state-of-the-art-cardinality-estimation-algorithm/)
4. [Wikipedia: HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog)
