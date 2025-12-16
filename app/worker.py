"""
RQ Worker for processing pipeline tasks.
"""
import os
from redis import Redis
from rq import Worker, Queue, Connection


def get_redis_connection() -> Redis:
    """Get Redis connection from environment."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url)


def main():
    """Main worker entry point."""
    redis_conn = get_redis_connection()
    
    with Connection(redis_conn):
        queues = [Queue("novel-engine")]
        worker = Worker(queues)
        print("Starting Novel Engine worker...")
        print(f"Listening on queues: {[q.name for q in queues]}")
        worker.work()


if __name__ == "__main__":
    main()
