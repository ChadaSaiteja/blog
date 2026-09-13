# HDFS - Hadoop Distributed File System

## GFS - Google File System

The OS follows the same file system concept: memory is divided into blocks (block size depends on the OS).

- Block size: 4KB
- Number of blocks = total memory / block size

### Example

A 12KB image uses 3 blocks. The image is divided into 3 chunks and stored randomly across the blocks.

While retrieving, we need a way to locate the chunks, so a main index holds the addresses of all the child block addresses.

### Scaling problem

What if the data that needs to be stored is more than the capacity? How do we handle this — add more storage?
That's costlier and raises issues with scalability.

Chunks are made and stored in chunk servers, and a main server sits in front. When you watch an image or video, the master server pulls it from the chunk server and displays it. Since we have multiple servers, a point of failure is expected — handling this is the biggest challenge, so Google introduced GFS.

### GFS

GFS makes multiple copies of the same chunk and stores them in different chunk servers. This process is called replication — based on the replication factor, chunks are copied to different servers.

But what if the server holding a replica goes down?

GFS handles this by having each chunk server send a heartbeat to the master. Based on this, the master updates its mapping table.

If the number of available replicas is less than the replication factor (RF), the chunks are copied to another chunk server. This way, it keeps trying to match the RF.

### What if the master dies?

The primary master constantly copies its state to a backup master, which contains most of the up-to-date data.

Both masters are monitored using heartbeats: user request -> check heartbeat -> use primary, or redirect to backup.

https://research.google/pubs/the-google-file-system/

using above paper and md fil