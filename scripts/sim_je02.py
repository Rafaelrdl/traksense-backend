#!/usr/bin/env python3
"""
Simulador MQTT para protocolo JE02 - Inversores IoT

Simula inversores JE02 publicando telemetria periódica via MQTT.

Características:
- Publica payload DATA a cada --period segundos
- INPUT1: 80% RUN (1), 20% STOP (0)
- INPUT2: 2-5% FAULT (1) por 30-60 segundos
- WRSSI: sinal WiFi aleatório entre -55 e -75 dBm
- VAR0: temperatura 21.0-26.0°C (210-260 raw, dividido por 10)
- VAR1: umidade 45-65% (450-650 raw, dividido por 10)
- RELE: estado do relé (0 ou 1)
- CNTSERR: contador de erros seriais
- UPTIME: uptime em segundos

Opcional:
- Subscribe em /cmd para receber comandos
- Reflete RELE baseado em comandos recebidos

Uso:
    # Simulador simples (1 device):
    python scripts/sim_je02.py --config sim_inv01.json --period 5
    
    # Múltiplos devices (7 inversores):
    python scripts/sim_je02.py --config configs/inv*.json --period 3
    
    # Com suporte a comandos:
    python scripts/sim_je02.py --config sim_inv01.json --listen-cmd

Formato do config JSON:
{
    "mqtt": {
        "host": "localhost",
        "port": 1883,
        "username": "t:demo:d:inv-01",
        "password": "secret123"
    },
    "device": {
        "name": "INV-01",
        "topic_base": "traksense/demo/plant-01/inv-01"
    }
}

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

import asyncio
import argparse
import json
import random
import time
import signal
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from aiomqtt import Client, MqttError
except ImportError:
    print("❌ Erro: biblioteca 'aiomqtt' não encontrada!")
    print("   Instale com: pip install aiomqtt")
    sys.exit(1)


class JE02Simulator:
    """
    Simulador de inversor JE02.
    """
    
    def __init__(self, config: Dict[str, Any], period: int, listen_cmd: bool = False):
        """
        Inicializa simulador.
        
        Args:
            config: Dicionário de configuração
            period: Período de publicação em segundos
            listen_cmd: Se deve escutar comandos em /cmd
        """
        self.config = config
        self.period = period
        self.listen_cmd = listen_cmd
        
        # Estado interno
        self.uptime = 0
        self.cntserr = 0
        self.rele_state = 0  # 0=OFF, 1=ON
        self.fault_until = 0  # Timestamp até quando device está em FAULT
        self.running = True
        
        # MQTT config
        mqtt = config['mqtt']
        self.mqtt_host = mqtt['host']
        self.mqtt_port = mqtt['port']
        self.mqtt_username = mqtt.get('username')
        self.mqtt_password = mqtt.get('password')
        
        # Device config
        device = config['device']
        self.device_name = device['name']
        self.topic_base = device['topic_base']
        self.topic_telem = f"{self.topic_base}/telem"
        self.topic_cmd = f"{self.topic_base}/cmd"
    
    def _generate_data(self) -> Dict[str, Any]:
        """
        Gera payload DATA simulado.
        
        Returns:
            Dict com payload DATA
        """
        now = int(time.time())
        
        # INPUT2: FAULT (2-5% de chance, duração 30-60s)
        if self.fault_until > now:
            input2 = 1  # Em FAULT
            input1 = 0  # Não pode estar RUN se está em FAULT
        else:
            # Chance de entrar em FAULT
            if random.random() < 0.03:  # 3% de chance
                self.fault_until = now + random.randint(30, 60)
                input2 = 1
                input1 = 0
            else:
                input2 = 0
                # INPUT1: RUN (80% chance)
                input1 = 1 if random.random() < 0.8 else 0
        
        # VAR0: Temperatura (21.0-26.0°C)
        var0 = random.randint(210, 260)  # Será dividido por 10 no adapter
        
        # VAR1: Umidade (45-65%)
        var1 = random.randint(450, 650)  # Será dividido por 10 no adapter
        
        # WRSSI: Sinal WiFi (-55 a -75 dBm)
        wrssi = random.randint(-75, -55)
        
        # CNTSERR: Incrementa raramente
        if random.random() < 0.05:  # 5% de chance
            self.cntserr += 1
        
        # Uptime
        self.uptime += self.period
        
        return {
            "DATA": {
                "TS": now,
                "INPUT1": input1,
                "INPUT2": input2,
                "VAR0": var0,
                "VAR1": var1,
                "WRSSI": wrssi,
                "RELE": self.rele_state,
                "CNTSERR": self.cntserr,
                "UPTIME": self.uptime
            }
        }
    
    def _generate_info(self) -> Dict[str, Any]:
        """
        Gera payload INFO (metadados).
        
        Returns:
            Dict com payload INFO
        """
        return {
            "INFO": {
                "FW_VERSION": "1.2.3",
                "HW_VERSION": "v1",
                "DEVICE_ID": self.device_name,
                "MODEL": "JE02-INVERTER"
            }
        }
    
    async def _publish_loop(self, client: Client):
        """
        Loop de publicação periódica.
        
        Args:
            client: Cliente MQTT
        """
        print(f"[{self.device_name}] 🚀 Publicando a cada {self.period}s em {self.topic_telem}")
        
        # Publicar INFO uma vez no início
        info_payload = self._generate_info()
        await client.publish(
            self.topic_telem,
            payload=json.dumps(info_payload),
            qos=1
        )
        print(f"[{self.device_name}] 📤 INFO publicado")
        
        # Loop de publicação DATA
        while self.running:
            # Gerar e publicar DATA
            data_payload = self._generate_data()
            
            await client.publish(
                self.topic_telem,
                payload=json.dumps(data_payload),
                qos=1
            )
            
            # Status para log
            data = data_payload['DATA']
            if data['INPUT2'] == 1:
                status = "FAULT"
            elif data['INPUT1'] == 1:
                status = "RUN"
            else:
                status = "STOP"
            
            print(
                f"[{self.device_name}] 📤 DATA: "
                f"status={status}, "
                f"temp={data['VAR0']/10:.1f}°C, "
                f"hum={data['VAR1']/10:.1f}%, "
                f"rssi={data['WRSSI']}dBm, "
                f"rele={self.rele_state}"
            )
            
            await asyncio.sleep(self.period)
    
    async def _cmd_listener(self, client: Client):
        """
        Escuta comandos em /cmd.
        
        Args:
            client: Cliente MQTT
        """
        if not self.listen_cmd:
            return
        
        print(f"[{self.device_name}] 👂 Escutando comandos em {self.topic_cmd}")
        
        await client.subscribe(self.topic_cmd, qos=1)
        
        async for msg in client.messages:
            try:
                cmd = json.loads(msg.payload)
                print(f"[{self.device_name}] 📥 CMD recebido: {cmd}")
                
                # Processar comando (exemplo: SET_RELE)
                if 'cmd' in cmd and cmd['cmd'] == 'SET_RELE':
                    new_state = cmd.get('value', 0)
                    self.rele_state = 1 if new_state else 0
                    print(f"[{self.device_name}] ⚡ RELE alterado para {self.rele_state}")
                    
                    # Publicar ACK
                    ack = {
                        "cmd_id": cmd.get('cmd_id', 'unknown'),
                        "ok": True,
                        "ts_exec": int(time.time())
                    }
                    topic_ack = f"{self.topic_base}/ack"
                    await client.publish(topic_ack, payload=json.dumps(ack), qos=1)
                    print(f"[{self.device_name}] ✅ ACK enviado")
            
            except Exception as e:
                print(f"[{self.device_name}] ❌ Erro ao processar comando: {e}")
    
    async def run(self):
        """
        Executa simulador.
        """
        print(f"[{self.device_name}] Conectando a {self.mqtt_host}:{self.mqtt_port}")
        
        # Configurar cliente MQTT
        client_kwargs = {
            "hostname": self.mqtt_host,
            "port": self.mqtt_port,
        }
        
        if self.mqtt_username:
            client_kwargs["username"] = self.mqtt_username
            client_kwargs["password"] = self.mqtt_password
        
        try:
            async with Client(**client_kwargs) as client:
                print(f"[{self.device_name}] ✅ Conectado!")
                
                # Criar tasks
                tasks = [
                    asyncio.create_task(self._publish_loop(client)),
                ]
                
                if self.listen_cmd:
                    tasks.append(asyncio.create_task(self._cmd_listener(client)))
                
                # Aguardar tasks
                await asyncio.gather(*tasks)
        
        except MqttError as e:
            print(f"[{self.device_name}] ❌ Erro MQTT: {e}")
        except Exception as e:
            print(f"[{self.device_name}] ❌ Erro: {e}")
    
    def stop(self):
        """Para o simulador."""
        self.running = False


async def main():
    """
    Função principal do simulador.
    """
    # Parse argumentos
    parser = argparse.ArgumentParser(
        description='Simulador MQTT para protocolo JE02',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Simular 1 device:
  python sim_je02.py --config inv01.json --period 5
  
  # Simular com suporte a comandos:
  python sim_je02.py --config inv01.json --listen-cmd
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Arquivo JSON de configuração (ex: inv01.json)'
    )
    
    parser.add_argument(
        '--period',
        type=int,
        default=5,
        help='Período de publicação em segundos (padrão: 5)'
    )
    
    parser.add_argument(
        '--listen-cmd',
        action='store_true',
        help='Escutar comandos em /cmd'
    )
    
    args = parser.parse_args()
    
    # Carregar configuração
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {args.config}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Criar simulador
    simulator = JE02Simulator(
        config=config,
        period=args.period,
        listen_cmd=args.listen_cmd
    )
    
    # Handler para SIGINT (Ctrl+C)
    def signal_handler(sig, frame):
        print("\n⏹️  Parando simulador...")
        simulator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Executar simulador
    print("="*70)
    print(f"🌟 SIMULADOR JE02 - {config['device']['name']}")
    print("="*70)
    await simulator.run()


if __name__ == '__main__':
    asyncio.run(main())
