---
layout: post
title: "Mastering Go Concurrency Patterns"
description: "A deep dive into Go channels, select blocks, and worker pools for highly concurrent programs."
date: 2026-08-11
categories:
  - Go
  - Concurrency
tags:
  - golang
  - backend
  - patterns
author: "Saiteja"
draft: false
---

Go's concurrency model is based on Communicating Sequential Processes (CSP). By using goroutines and channels, Go makes it straightforward to write safe, high-performance concurrent software.

In this guide, we'll examine how channels work under the hood and implement a resilient worker pool pattern.

## Goroutines vs Threads

Unlike OS threads which are managed by the kernel, goroutines are managed by the Go runtime scheduler.
- **Memory Footprint:** A thread has a fixed stack (typically 1-2MB). A goroutine starts with a small dynamic stack (2KB) that grows and shrinks as needed.
- **Context Switching:** Switching goroutines is done in user space and is much faster than switching kernel threads.

## The Worker Pool Pattern

A worker pool limits resource usage (such as database connections or memory) by spawning a fixed number of goroutines that pull tasks from a shared channel.

Here is a standard worker pool implementation in Go:

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID    int
	Value int
}

type Result struct {
	JobID  int
	Output int
	Err    error
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		fmt.Printf("Worker %d starting job %d\n", id, job.ID)
		time.Sleep(100 * time.Millisecond)
		
		results <- Result{
			JobID:  job.ID,
			Output: job.Value * 2,
			Err:    nil,
		}
		fmt.Printf("Worker %d finished job %d\n", id, job.ID)
	}
}

func main() {
	numJobs := 10
	numWorkers := 3

	jobs := make(chan Job, numJobs)
	results := make(chan Result, numJobs)

	var wg sync.WaitGroup

	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, jobs, results, &wg)
	}

	for j := 1; j <= numJobs; j++ {
		jobs <- Job{ID: j, Value: j}
	}
	close(jobs)

	go func() {
		wg.Wait()
		close(results)
	}()

	for result := range results {
		fmt.Printf("Job result: Job %d -> Output %d\n", result.JobID, result.Output)
	}
}
```

## Production Considerations

When deploying worker pools to production:
1. **Channel Blocking:** Be careful with unbuffered channels. If the results channel is full and has no reader, the workers will block.
2. **Context Cancellation:** Use `context.Context` to propagate cancellations and prevent goroutine leaks when a request is cancelled or timed out.
3. **Panic Recovery:** Recover from panics inside workers to keep the pool active.

## References
1. [Effective Go - Concurrency](https://golang.org/doc/effective_go#concurrency)
2. [Go Concurrency Patterns](https://talks.golang.org/2012/concurrency.slide) by Rob Pike
