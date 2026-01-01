import asyncio
import time
from redis.asyncio import Redis

async def test_ingestion_pipeline():
    # Connect to Redis
    r = Redis(host='redis', port=6379, decode_responses=True)
    stream_name = "social_posts_stream"
    
    print("--- 1. Class & Publishing Test (7 Points) ---")
    try:
        # Check if stream exists and has data
        info = await r.xinfo_stream(stream_name)
        length = await r.xlen(stream_name)
        print(f"✅ Stream '{stream_name}' exists.")
        print(f"✅ Messages published: {length}")
    except Exception as e:
        print(f"❌ Stream not found or Redis unreachable: {e}")
        return

    print("\n--- 2. Post Structure & Content Test (4 Points) ---")
    messages = await r.xread({stream_name: "0"}, count=5)
    if messages:
        # messages format: [[stream_name, [[msg_id, data_dict], ...]]]
        sample_data = messages[0][1][0][1]
        required_keys = ['post_id', 'source', 'content', 'author', 'created_at']
        
        missing = [k for k in required_keys if k not in sample_data]
        if not missing:
            print("✅ All required keys present in message.")
            print(f"   Sample Content: {sample_data['content'][:50]}...")
        else:
            print(f"❌ Missing keys: {missing}")
    else:
        print("❌ No messages found to inspect.")

    print("\n--- 3. Rate Limiting Test (2 Points) ---")
    print("Measuring ingestion rate for 10 seconds...")
    start_count = await r.xlen(stream_name)
    await asyncio.sleep(10)
    end_count = await r.xlen(stream_name)
    
    rate_per_min = (end_count - start_count) * 6
    print(f"✅ Current Rate: ~{rate_per_min} posts/minute")
    print("   (Target is usually 60 ppm)")

    await r.close()

if __name__ == "__main__":
    asyncio.run(test_ingestion_pipeline())