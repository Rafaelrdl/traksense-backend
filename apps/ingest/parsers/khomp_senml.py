"""
Parser para gateways LoRaWAN Khomp com formato SenML.

Este parser processa payloads no formato SenML (Sensor Measurement Lists)
conforme RFC 8428, usado pelos gateways Khomp.
"""
import datetime
import logging
from typing import Dict, Any, List, Optional

from apps.ingest.parsers import PayloadParser

logger = logging.getLogger(__name__)


class KhompSenMLParser(PayloadParser):
    """
    Parser para gateways LoRaWAN Khomp que usam formato SenML.
    
    Formato SenML (RFC 8428):
    - bn: Base Name (MAC do dispositivo)
    - bt: Base Time (timestamp em segundos)
    - n: Name (identificador da medição)
    - v: Value (valor numérico)
    - vs: String Value (valor texto)
    - vb: Boolean Value (valor booleano)
    - u: Unit (unidade de medida)
    
    Exemplo de payload:
    [
        {"bn": "4b686f6d70107115", "bt": 1552594568},
        {"n": "model", "vs": "nit20l"},
        {"n": "rssi", "u": "dBW", "v": -61},
        {"n": "A", "u": "Cel", "v": 23.35},
        {"n": "A", "u": "%RH", "v": 64.0},
        {"n": "283286b20a000036", "u": "Cel", "v": 30.75},
        {"n": "gateway", "vs": "000D6FFFFE642E70"}
    ]
    """
    
    # Mapeamento de unidades SenML para unidades padronizadas
    UNIT_MAPPING = {
        'Cel': 'celsius',
        '%RH': 'percent_rh',
        'dBW': 'dBW',
        'W': 'watt',
        'V': 'volt',
        'A': 'ampere',
        'K': 'kelvin',
        'lx': 'lux',
        'm': 'meter',
        'kg': 'kilogram',
        'g': 'gram',
        's': 'second',
        'Ohm': 'ohm',
        'm2': 'square_meter',
        'm3': 'cubic_meter',
        'l': 'liter',
        'm/s': 'meters_per_second',
        'm/s2': 'meters_per_second_squared',
        'm3/s': 'cubic_meters_per_second',
        'l/s': 'liters_per_second',
        'count': 'count',
        '%': 'percent',
        '%EL': 'energy_level_percent'
    }
    
    # Mapeamento de tipos de sensor baseado no nome
    SENSOR_TYPE_MAPPING = {
        'A': 'ambient',  # Sensor ambiente (temperatura/umidade)
        'B': 'ambient',
        'C': 'ambient',
        'C1': 'binary_counter',  # Contador binário
        'C2': 'binary_counter',
        'rssi': 'signal_strength',
        'model': 'device_info',
        'gateway': 'gateway_info'
    }
    
    def can_parse(self, payload: Dict[str, Any], topic: str) -> bool:
        """
        Verifica se o payload é no formato SenML da Khomp.
        
        Critérios:
        1. Payload deve ser uma lista (array JSON)
        2. Primeiro elemento deve ter 'bn' (basename) e 'bt' (basetime)
        3. Elementos devem ter estrutura SenML (n, v/vs/vb, u opcional)
        """
        # Se o payload vem encapsulado do EMQX
        if isinstance(payload, dict) and 'payload' in payload:
            inner_payload = payload.get('payload')
        else:
            inner_payload = payload
        
        # Verificar se é uma lista
        if not isinstance(inner_payload, list):
            return False
        
        if len(inner_payload) < 2:
            return False
        
        # Verificar primeiro elemento (deve ter bn e bt)
        first_element = inner_payload[0]
        if not isinstance(first_element, dict):
            return False
        
        if 'bn' not in first_element or 'bt' not in first_element:
            return False
        
        # Verificar se tem elementos com estrutura SenML
        for element in inner_payload[1:]:
            if isinstance(element, dict) and 'n' in element:
                # Deve ter pelo menos um valor (v, vs, ou vb)
                if any(k in element for k in ['v', 'vs', 'vb']):
                    logger.info("✅ Payload identificado como formato SenML da Khomp")
                    return True
        
        return False
    
    def parse(self, payload: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Processa payload SenML e converte para formato padrão TrakSense.
        """
        # Extrair o payload real (pode vir encapsulado do EMQX)
        if isinstance(payload, dict) and 'payload' in payload:
            senml_data = payload.get('payload')
            emqx_wrapper = payload
        else:
            senml_data = payload
            emqx_wrapper = None
        
        if not isinstance(senml_data, list) or len(senml_data) < 1:
            raise ValueError("Payload SenML inválido: deve ser uma lista")
        
        # Extrair base name e base time do primeiro elemento
        base_element = senml_data[0]
        base_name = base_element.get('bn')  # MAC do dispositivo
        base_time = base_element.get('bt')  # Timestamp em segundos
        
        if not base_name:
            raise ValueError("Payload SenML inválido: 'bn' não encontrado")
        
        # Converter base_time para datetime
        if base_time:
            try:
                timestamp = datetime.datetime.fromtimestamp(base_time)
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao converter base_time: {e}, usando timestamp atual")
                timestamp = datetime.datetime.now()
        else:
            timestamp = datetime.datetime.now()
        
        # Informações extraídas
        device_id = base_name
        gateway_id = None
        model = None
        sensors = []
        
        # Processar cada medição
        for element in senml_data[1:]:
            if not isinstance(element, dict):
                continue
            
            name = element.get('n')
            if not name:
                continue
            
            # Identificar tipo de informação
            if name == 'model':
                model = element.get('vs')
                logger.info(f"📱 Modelo do dispositivo: {model}")
                continue
            elif name == 'gateway':
                gateway_id = element.get('vs')
                logger.info(f"🌐 Gateway ID: {gateway_id}")
                continue
            elif name == 'rssi':
                # RSSI é uma medição especial do sinal
                sensor_reading = self._create_sensor_reading(
                    sensor_id=f"{base_name}_rssi",
                    name=name,
                    value=element.get('v'),
                    unit=element.get('u', 'dBW'),
                    sensor_type='signal_strength'
                )
                if sensor_reading:
                    sensors.append(sensor_reading)
                continue
            
            # Processar medições de sensores
            sensor_reading = self._process_sensor_element(element, base_name)
            if sensor_reading:
                sensors.append(sensor_reading)
        
        # Adicionar metadados ao resultado
        result = {
            'device_id': device_id,
            'timestamp': timestamp,
            'sensors': sensors,
            'metadata': {
                'model': model,
                'gateway_id': gateway_id,
                'format': 'senml',
                'base_time': base_time
            }
        }
        
        logger.info(
            f"✅ KhompSenMLParser: device={device_id}, "
            f"sensors={len(sensors)}, gateway={gateway_id}, model={model}"
        )
        
        return result
    
    def _process_sensor_element(self, element: Dict[str, Any], base_name: str) -> Optional[Dict[str, Any]]:
        """
        Processa um elemento de sensor SenML.
        
        Lida com diferentes tipos de valores:
        - v: valor numérico
        - vs: valor string
        - vb: valor booleano
        """
        name = element.get('n')
        
        # Determinar o sensor_id
        # Se o nome for um MAC address (DS18B20), usar como está
        if self._is_mac_address(name):
            sensor_id = name
            sensor_type = 'temperature'  # DS18B20 é sempre temperatura
        else:
            # Sensor interno do dispositivo (A, B, C1, etc.)
            sensor_id = f"{base_name}_{name}"
            sensor_type = self.SENSOR_TYPE_MAPPING.get(name, 'unknown')
        
        # Extrair valor
        value = None
        value_type = None
        
        if 'v' in element:
            value = element['v']
            value_type = 'numeric'
        elif 'vs' in element:
            value = element['vs']
            value_type = 'string'
        elif 'vb' in element:
            value = 1 if element['vb'] else 0  # Converter booleano para numérico
            value_type = 'boolean'
        
        if value is None:
            return None
        
        # Extrair unidade
        unit = element.get('u')
        
        # Para sensores com múltiplas medições (ex: sensor A com temp e umidade)
        # precisamos diferenciar pelo tipo de unidade
        if name in ['A', 'B', 'C'] and unit:
            if unit == 'Cel':
                sensor_id = f"{sensor_id}_temp"
                sensor_type = 'temperature'
            elif unit == '%RH':
                sensor_id = f"{sensor_id}_humid"
                sensor_type = 'humidity'
            elif unit == 'count':
                sensor_id = f"{sensor_id}_count"
                sensor_type = 'counter'
        
        return self._create_sensor_reading(
            sensor_id=sensor_id,
            name=name,
            value=value,
            unit=unit,
            sensor_type=sensor_type,
            value_type=value_type
        )
    
    def _create_sensor_reading(self, sensor_id: str, name: str, value: Any,
                              unit: Optional[str], sensor_type: str,
                              value_type: str = 'numeric') -> Optional[Dict[str, Any]]:
        """
        Cria um reading de sensor no formato padrão TrakSense.
        """
        # Converter unidade SenML para padrão
        standard_unit = self.UNIT_MAPPING.get(unit, unit) if unit else None
        
        # Garantir que o valor seja numérico quando possível
        numeric_value = value
        if value_type == 'string':
            try:
                numeric_value = float(value)
                value_type = 'numeric'
            except (ValueError, TypeError):
                # Manter como string se não for conversível
                # Para strings, usamos 0 como placeholder no campo value
                numeric_value = 0
        
        reading = {
            'sensor_id': sensor_id,
            'value': numeric_value,
            'labels': {
                'name': name,
                'type': sensor_type,
                'value_type': value_type
            }
        }
        
        if standard_unit:
            reading['labels']['unit'] = standard_unit
        
        if unit and unit != standard_unit:
            reading['labels']['original_unit'] = unit
        
        # Adicionar valor original se for diferente
        if value_type != 'numeric':
            reading['labels']['original_value'] = str(value)
        
        return reading
    
    def _is_mac_address(self, value: str) -> bool:
        """
        Verifica se o valor parece ser um endereço MAC.
        
        Exemplos válidos:
        - 283286b20a000036 (DS18B20)
        - 000D6FFFFE642E70 (Gateway)
        - 4b686f6d70107115 (Device)
        """
        if not isinstance(value, str):
            return False
        
        # Remover possíveis separadores
        clean_value = value.replace(':', '').replace('-', '').upper()
        
        # MAC address tem 12 ou 16 caracteres hexadecimais
        if len(clean_value) not in [12, 16]:
            return False
        
        # Verificar se todos os caracteres são hexadecimais
        try:
            int(clean_value, 16)
            return True
        except ValueError:
            return False
