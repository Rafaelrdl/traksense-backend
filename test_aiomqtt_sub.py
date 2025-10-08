#!/usr/bin/env python3
"""
Script de teste para verificar subscriptions com aiomqtt 2.x.
"""
import asyncio
from aiomqtt import Client

async def test_subscribe():
    print("🔌 Conectando ao EMQX...")
    async with Client(hostname="emqx", port=1883) as client:
        print("✅ Conectado!")
        
        # Aguardar um pouco após conexão
        await asyncio.sleep(0.5)
        
        print("📋 Subscrevendo a traksense/+/+/+/telem...")
        result = await client.subscribe("traksense/+/+/+/telem", qos=1)
        print(f"✅ Subscribe retornou: {result}")
        
        # Aguardar propagação da subscription
        await asyncio.sleep(1)
        
        print("⏳ Aguardando mensagens...")
        count = 0
        async for msg in client.messages:
            print(f"✉️ Mensagem {count+1}: topic={msg.topic}, size={len(msg.payload)}")
            count += 1
            if count >= 5:  # Stop após 5 mensagens
                break

if __name__ == "__main__":
    asyncio.run(test_subscribe())
