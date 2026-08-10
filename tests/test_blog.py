import unittest
import os
import sys
import tempfile
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "blog"))

from quality import BlogQualityAnalyzer
from server import parse_markdown_file, write_markdown_file

class TestBlogAutomation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.test_dir.cleanup()

    def test_slug_generation(self):
        title = "Understanding Kafka! Message (Ordering) & Execution"
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug).strip("-")
        self.assertEqual(slug, "understanding-kafka-message-ordering-execution")

    def test_frontmatter_read_write(self):
        temp_filepath = os.path.join(self.test_dir.name, "test-post.md")
        metadata = {
            "layout": "post",
            "title": "Unit Test Blog Post",
            "date": "2026-08-09",
            "categories": ["Testing", "Python"],
            "tags": ["unittest", "ci"],
            "author": "Saiteja",
            "draft": True
        }
        body = "This is the body of the unit test post. It contains some markdown text."
        
        write_markdown_file(temp_filepath, metadata, body)
        read_meta, read_body = parse_markdown_file(temp_filepath)
        
        self.assertEqual(read_meta["title"], metadata["title"])
        self.assertEqual(read_meta["date"], metadata["date"])
        self.assertEqual(read_meta["author"], metadata["author"])
        self.assertEqual(read_meta["draft"], metadata["draft"])
        self.assertEqual(read_meta["categories"], metadata["categories"])
        self.assertEqual(read_meta["tags"], metadata["tags"])
        self.assertEqual(read_body.strip(), body.strip())

    def test_quality_analyzer_scoring(self):
        temp_filepath = os.path.join(self.test_dir.name, "test-quality-post.md")
        
        weak_content = """---
layout: post
title: "Short"
description: ""
date: 2026-08-09
categories: []
tags: []
author: ""
draft: true
---
Too short body content.
"""
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(weak_content)
            
        analyzer = BlogQualityAnalyzer(temp_filepath)
        analyzer.analyze()
        weak_score = analyzer.get_total_score()
        
        self.assertTrue(weak_score < 70)
        self.assertTrue(any("Missing description" in w or "SEO: Missing description" in w for w in analyzer.warnings))
        self.assertTrue(any("Add at least 1 category" in w or "Quality: Categories are missing" in w for w in analyzer.warnings))

        strong_content = """---
layout: post
title: "Implementing Resilient Redis Caching"
description: "A comprehensive guide on setting up Redis cache strategies, TTL rules, and key expulsion policies in Go."
date: 2026-08-09
categories:
  - Cache
  - Backend
tags:
  - redis
  - golang
  - databases
author: "Saiteja"
draft: false
---
Caching is an essential component of high-performance backend systems. It helps reduce database read loads and improves response times for frequently requested assets. In modern distributed systems, data stores like Redis and Memcached are frequently used to handle millions of queries per second. While Memcached is highly efficient for simple key-value structures, Redis offers rich data structures such as lists, sets, sorted sets, and hashes, making it much more versatile for complex caching patterns and transient state management.

In this guide, we will look at how to implement a cache-aside strategy in Go using Redis. Cache-aside is highly resilient because a caching layer failure does not crash the application; instead, the application falls back directly to querying the database, albeit with increased latency.

## The Cache Aside Pattern

The cache-aside pattern is the most common caching pattern:
- The application tries to read from the cache first.
- If it is a cache hit, return the data.
- If it is a cache miss, read from the database, write to the cache, and return the data.

This process ensures that data is only loaded into the cache when it is explicitly requested, which helps conserve caching memory resources. However, it can lead to a slight overhead on cache misses, as the application has to query both the cache and the primary database. Furthermore, we must establish dynamic cache invalidation rules so that updates to the database are either written to the cache immediately or the cache keys are evicted to prevent returning stale data to users.

## Implementation in Go

Here is how to set up the Redis client and implement cache-aside logic:

```go
package main

import (
	"context"
	"fmt"
	"time"
	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

func main() {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	
	err := rdb.Set(ctx, "user:101", "{id: 101, name: 'Saiteja'}", 5*time.Minute).Err()
	if err != nil {
		panic(err)
	}
	
	fmt.Println("Cache set successfully!")
}
```

## Key Takeaways

When deploying a production cache, keep these critical architectural patterns in mind:

- **TTL Bounds:** Always set a Time-To-Live (TTL) on cached keys to prevent stale data. A good practice is to set a randomized jitter on TTLs (e.g. 5 minutes +/- 30 seconds) to prevent all keys from expiring at the exact same moment, which can cause a sudden traffic spike to your database.

- **Cache Stampede:** Use mutexes or singleflight in Go to prevent multiple concurrent goroutines from fetching database resources on cache misses. This ensures only one worker queries the database, while other requests block and wait for the result.

- **Write Invalidation:** Decide on a write policy. Under a Write-Through cache scheme, updates are written to the database and the cache simultaneously. Under a Write-Back cache, updates are written to the cache first and asynchronously flushed to the database. Choose the policy that matches your read-to-write ratio.

- **Connection Pools:** Ensure that your Go redis client connection pool size is configured appropriately to support high concurrency under peak traffic scenarios without leaking socket file descriptors.

## References
1. [Redis Official Documentation - Caching Guide](https://redis.io/docs/manual/client-side-caching/)
2. [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) by Martin Kleppmann.
"""
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(strong_content)
            
        analyzer_strong = BlogQualityAnalyzer(temp_filepath)
        analyzer_strong.analyze()
        strong_score = analyzer_strong.get_total_score()
        
        print("WARNINGS GATHERED:", analyzer_strong.warnings)
        self.assertTrue(strong_score >= 90)
        self.assertEqual(len(analyzer_strong.warnings), 0)

if __name__ == "__main__":
    unittest.main()
