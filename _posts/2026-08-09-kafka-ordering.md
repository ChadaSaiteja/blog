---
layout: post
title: "Understanding Kafka Message Ordering"
description: "A practical explanation of Kafka ordering guarantees and how to prevent event status regression."
date: 2026-08-09
updated: 2026-08-09
categories:
  - Kafka
  - Backend
tags:
  - kafka
  - microservices
  - event-driven
author: "Saiteja"
draft: false
---

In event-driven architectures using Apache Kafka, maintaining message ordering is a common requirement. For example, if a user updates their profile twice in quick succession, we must ensure the second update is not overwritten by the first due to out-of-order delivery.

In this article, we'll explain how Kafka guarantees ordering, look at a common production problem (Salesforce status regression), and implement an idempotency/sequencing check in TypeScript.

## The Problem: Event Status Regression

Imagine a system where order updates are produced by an upstream service and sent to Salesforce. The order progresses through statuses:
1. `Pre-fieldCompleted`
2. `ReadyForInstall`
3. `Completed`

Due to network latency, retries, or multiple producers, a `ReadyForInstall` event might reach the consumer *before* `Pre-fieldCompleted`. If we simply write whatever status arrives, Salesforce might transition from `ReadyForInstall` back to `Pre-fieldCompleted`—a status regression that breaks business logic.

## What Kafka Guarantees

Kafka guarantees message ordering **only within a single partition**. If events are sent to different partitions, there is no ordering guarantee between them.

To ensure related events are processed in order:
1. **Partition Key:** Use a consistent key (like `orderId`) so all events for that order route to the same partition.
2. **Single Consumer Thread (per partition):** Within a partition, events are stored and delivered in write order.

## Implementation: Preventing Status Regression

Even with partition keys, we must protect against:
- Multiple producers producing out of order.
- Consumer retries of failed events.

The solution is to maintain a state hierarchy and check the status order on the consumer side. Here is a TypeScript example:

```typescript
const StatusSequence: Record<string, number> = {
  'Pre-fieldCompleted': 1,
  'ReadyForInstall': 2,
  'Completed': 3
};

interface OrderEvent {
  orderId: string;
  status: string;
  timestamp: number;
}

class SalesforceUpdater {
  private currentStatusCache = new Map<string, string>();

  public async handleOrderEvent(event: OrderEvent): Promise<void> {
    const { orderId, status } = event;
    const currentStatus = this.currentStatusCache.get(orderId);

    if (currentStatus) {
      const currentRank = StatusSequence[currentStatus] || 0;
      const incomingRank = StatusSequence[status] || 0;

      if (incomingRank <= currentRank) {
        console.warn(`[Ignore] Stale event received. Current: ${currentStatus}, Incoming: ${status}`);
        return;
      }
    }

    await this.updateSalesforce(orderId, status);
    this.currentStatusCache.set(orderId, status);
  }

  private async updateSalesforce(orderId: string, status: string): Promise<void> {
    console.log(`[Success] Updated order ${orderId} to ${status}`);
  }
}
```

## Key Takeaways

- **Order Key:** Always use a consistent partition key to route related events to the same partition.
- **State Guarding:** Implement sequence ranking on the consumer side to discard stale status updates.
- **Idempotence:** Make your consumer idempotent by logging event offsets or message IDs.

## References
1. [Apache Kafka Documentation - Design](https://kafka.apache.org/documentation/#design)
2. [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) by Martin Kleppmann.
