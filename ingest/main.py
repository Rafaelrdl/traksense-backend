"""
TrakSense Ingest Service
Consumes MQTT messages and persists to TimescaleDB.
This is a minimal version for infrastructure validation.
"""
import os
import asyncio
import aiomqtt

MQTT_URL = os.getenv("MQTT_URL", "mqtt://emqx:1883")
HOST = MQTT_URL.replace("mqtt://", "").split(":")[0]
PORT = int(MQTT_URL.split(":")[-1])


async def main():
    """Connect to MQTT broker and log success."""
    print(f"[ingest] connecting to MQTT at {HOST}:{PORT} ...")
    try:
        async with aiomqtt.Client(hostname=HOST, port=PORT) as client:
            print("[ingest] connected ok (dev)")
            # Keep alive for a moment to verify connection
            await asyncio.sleep(1)
            print("[ingest] connection verified, exiting gracefully")
    except Exception as e:
        print(f"[ingest] ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
