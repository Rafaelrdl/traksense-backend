"""
Configuração do serviço de ingest assíncrono.

Carrega variáveis de ambiente e define constantes de operação.
"""

from dataclasses import dataclass
import os


@dataclass
class Config:
    """
    Configuração centralizada do serviço de ingest.
    
    Atributos:
        mqtt_url: URL do broker MQTT (ex: mqtt://emqx:1883)
        topics: Lista de tópicos para subscrever
        qos: QoS do MQTT (0, 1 ou 2)
        queue_max: Tamanho máximo da fila interna (backpressure)
        batch_size: Número de mensagens para flush
        batch_ms: Tempo máximo (ms) antes de forçar flush
        db_url: URL de conexão do PostgreSQL
        db_pool_min: Tamanho mínimo do pool de conexões
        db_pool_max: Tamanho máximo do pool de conexões
        metrics_port: Porta para expor métricas Prometheus
    """
    
    # MQTT Configuration
    mqtt_url: str = os.getenv("MQTT_URL", "mqtt://emqx:1883")
    topics: list[str] = None  # Processado no __post_init__
    qos: int = int(os.getenv("MQTT_QOS", "1"))
    
    # Backpressure & Batching
    queue_max: int = int(os.getenv("INGEST_QUEUE_MAX", "50000"))
    batch_size: int = int(os.getenv("INGEST_BATCH_SIZE", "800"))
    batch_ms: int = int(os.getenv("INGEST_BATCH_MS", "250"))
    
    # Database
    db_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/traksense")
    db_pool_min: int = int(os.getenv("DB_POOL_MIN", "2"))
    db_pool_max: int = int(os.getenv("DB_POOL_MAX", "8"))
    
    # Observability
    metrics_port: int = int(os.getenv("METRICS_PORT", "9100"))
    
    def __post_init__(self):
        """Parse topics após inicialização."""
        topics_env = os.getenv("MQTT_TOPICS", "traksense/+/+/+/telem,traksense/+/+/+/ack")
        self.topics = [t.strip() for t in topics_env.split(",") if t.strip()]
        
        # Validações básicas
        if not self.topics:
            raise ValueError("MQTT_TOPICS não pode estar vazio")
        
        if not self.db_url:
            raise ValueError("DATABASE_URL é obrigatório")
        
        if self.batch_size < 1:
            raise ValueError("INGEST_BATCH_SIZE deve ser >= 1")
        
        if self.batch_ms < 1:
            raise ValueError("INGEST_BATCH_MS deve ser >= 1")
    
    def __repr__(self) -> str:
        """Representação segura (oculta credenciais do DB)."""
        db_safe = self.db_url.split("@")[-1] if "@" in self.db_url else self.db_url
        return (
            f"Config(mqtt_url={self.mqtt_url}, topics={len(self.topics)} tópicos, "
            f"qos={self.qos}, queue_max={self.queue_max}, batch_size={self.batch_size}, "
            f"batch_ms={self.batch_ms}, db={db_safe}, metrics_port={self.metrics_port})"
        )
