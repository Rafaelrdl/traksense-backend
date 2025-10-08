"""
Services - Devices App

Serviços de lógica de negócio para dispositivos IoT.
Contém funções para:
    - Provisionamento automático de Points e DashboardConfig (Fase 2)
    - Provisionamento de credenciais MQTT no EMQX (Fase 3)

IMPORTANTE: 
    - Sempre chamar provision_device_from_template() após criar um Device
      para gerar automaticamente Points e DashboardConfig.
    - Chamar provision_emqx_for_device() para criar credenciais MQTT e ACL.

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2 + Fase 3)
"""

import secrets
import logging
from django.db import transaction
from .models import Point, PointTemplate, Device
from .provisioning.factory import get_provisioner
from .provisioning.emqx import EmqxCredentials, EmqxProvisioningError


logger = logging.getLogger(__name__)


@transaction.atomic
def provision_device_from_template(
    device: Device,
    contracted_points: list[str] | None = None
):
    """
    Provisiona um Device criando Points e DashboardConfig automaticamente.
    
    Esta função deve ser chamada após criar um Device para:
    1. Instanciar Points a partir dos PointTemplates do DeviceTemplate
    2. Gerar o DashboardConfig filtrado por pontos contratados
    
    Args:
        device: Instância de Device a ser provisionada
        contracted_points: Lista opcional de nomes de pontos contratados.
                          Se None, todos os pontos são contratados.
                          Se lista, apenas pontos nesta lista são marcados como contratados.
    
    Comportamento:
        - Busca todos os PointTemplates do DeviceTemplate do device
        - Filtra por contracted_points se fornecido
        - Cria Points (bulk_create com ignore_conflicts para idempotência)
        - Chama dashboards.services.instantiate_dashboard_config()
    
    Exemplo:
        from devices.models import Device, DeviceTemplate
        from devices.services import provision_device_from_template
        
        template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
        device = Device.objects.create(
            template=template,
            name='Inversor 01 - Sala A'
        )
        
        # Provisionar todos os pontos
        provision_device_from_template(device)
        
        # Ou provisionar apenas alguns pontos
        provision_device_from_template(device, contracted_points=['status', 'fault'])
    """
    
    # 1) Criar Points a partir dos PointTemplates
    query = PointTemplate.objects.filter(device_template=device.template)
    
    if contracted_points is not None:
        query = query.filter(name__in=contracted_points)
    
    points_to_create = []
    for pt in query:
        # Determinar se o ponto está contratado
        is_contracted = (
            contracted_points is None or
            pt.name in contracted_points
        )
        
        points_to_create.append(Point(
            device=device,
            template=pt,
            name=pt.name,
            label=pt.label,
            unit=pt.unit,
            polarity=pt.polarity,
            limits=pt.default_limits or {},
            is_contracted=is_contracted,
        ))
    
    # Bulk create com ignore_conflicts para idempotência
    # (se rodar duas vezes, não duplica)
    Point.objects.bulk_create(points_to_create, ignore_conflicts=True)
    
    # 2) Gerar DashboardConfig
    from apps.dashboards.services import instantiate_dashboard_config
    instantiate_dashboard_config(device)


# ============================================================================
# Provisionamento EMQX (Fase 3)
# ============================================================================

def generate_client_id(tenant_id: str, site_slug: str, device_id: str) -> str:
    """
    Gera ClientID único para dispositivo MQTT.
    
    Formato: ts-<tenant_short>-<device_short>-<random>
    Exemplo: ts-1a2b3c4d-9f8e7d6c-a1b2c3d4
    
    Args:
        tenant_id: UUID do tenant (como string)
        site_slug: Slug do site
        device_id: UUID do device (como string)
    
    Returns:
        ClientID único e válido (sem espaços, #, +, /)
    
    Validação:
        - Máximo 23 caracteres (MQTT spec: 1-23 chars)
        - Apenas alfanuméricos e hífens
        - Prefixo 'ts-' identifica plataforma TrakSense
    
    Exemplo:
        client_id = generate_client_id(
            tenant_id="1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
            site_slug="factory-sp",
            device_id="9f8e7d6c-5b4a-3210-fedc-ba0987654321"
        )
        # Resultado: "ts-1a2b3c4d-9f8e7d6c-a1b2c3d4"
    """
    # Extrair primeiros 8 caracteres de cada UUID (suficiente para unicidade)
    tenant_short = tenant_id.replace('-', '')[:8]
    device_short = device_id.replace('-', '')[:8]
    
    # Sufixo aleatório (8 chars hex = 4 bytes)
    random_suffix = secrets.token_hex(4)
    
    # Montar ClientID: ts-{tenant}-{device}-{random}
    client_id = f"ts-{tenant_short}-{device_short}-{random_suffix}"
    
    # Validar comprimento (MQTT spec: máx 23 chars)
    if len(client_id) > 23:
        # Truncar se necessário (não deve acontecer com formato atual)
        logger.warning(f"ClientID muito longo ({len(client_id)} chars), truncando: {client_id}")
        client_id = client_id[:23]
    
    logger.debug(f"ClientID gerado: {client_id} (tenant={tenant_short}, device={device_short})")
    
    return client_id


def provision_emqx_for_device(
    device: Device,
    site_slug: str,
    password_length: int = 20
) -> dict[str, any]:
    """
    Provisiona credenciais MQTT no EMQX para um dispositivo.
    
    Cria:
        1. Usuário no sistema de autenticação do EMQX
        2. ACL mínima (publish/subscribe apenas nos tópicos do device)
        3. Atualiza campos credentials_id e topic_base no Device
    
    Args:
        device: Instância de Device a ser provisionada
        site_slug: Slug do site (para montar topic_base)
        password_length: Comprimento da senha gerada (mínimo 16, padrão 20)
    
    Returns:
        Dicionário com informações de conexão MQTT:
        {
            'mqtt': {
                'host': 'emqx.local',
                'port': 1883,
                'client_id': 'ts-...',
                'username': 't:<tenant>:d:<device>',
                'password': '<senha_gerada>'  # ATENÇÃO: salvar com segurança!
            },
            'topics': {
                'publish': ['traksense/.../state', ...],
                'subscribe': ['traksense/.../cmd']
            },
            'lwt': {
                'topic': 'traksense/.../state',
                'retain': True,
                'payload': '{"online": false}',
                'qos': 1
            }
        }
    
    Raises:
        EmqxProvisioningError: Falha ao provisionar no EMQX
        ValueError: Parâmetros inválidos
    
    Comportamento:
        - Idempotente: pode ser chamado múltiplas vezes (atualiza senha)
        - Persiste apenas username no campo credentials_id do Device
        - Password retornado deve ser salvo com segurança (cifrado ou exibido 1x)
        - ACL mínima: apenas prefixo do próprio device (sem wildcards #/+)
    
    Exemplo:
        from devices.models import Device
        from devices.services import provision_emqx_for_device
        
        device = Device.objects.get(id='...')
        mqtt_info = provision_emqx_for_device(device, site_slug='factory-sp')
        
        # Salvar password com segurança (ex: secrets manager)
        save_device_password(device.id, mqtt_info['mqtt']['password'])
        
        # Ou exibir apenas 1x para o operador
        print(f"⚠️ Senha gerada (salve com segurança): {mqtt_info['mqtt']['password']}")
    
    Segurança:
        ⚠️ CRÍTICO: A senha retornada deve ser:
            - Salva em secrets manager (ex: AWS Secrets, Azure KeyVault)
            - OU exibida apenas 1x ao operador e nunca mais recuperável
            - NUNCA armazenar em plain-text no banco de dados
            - Em produção, considerar rotação automática de senhas
    """
    # Validações
    if not device:
        raise ValueError("Device não fornecido")
    
    if not site_slug or not site_slug.strip():
        raise ValueError("site_slug não fornecido ou vazio")
    
    if password_length < 16:
        raise ValueError(f"password_length deve ser >= 16 (fornecido: {password_length})")
    
    # Obter tenant do connection (multi-tenancy por schema)
    from django.db import connection
    tenant_schema = connection.schema_name
    
    # Gerar credenciais
    username = f"t:{tenant_schema}:d:{device.id}"
    password = secrets.token_urlsafe(password_length)
    client_id = generate_client_id(
        tenant_id=tenant_schema,
        site_slug=site_slug,
        device_id=str(device.id)
    )
    
    creds = EmqxCredentials(
        username=username,
        password=password,
        client_id=client_id
    )
    
    # Obter provisioner (via factory)
    provisioner = get_provisioner()
    
    # Montar topic_base
    topic_base = f"traksense/{tenant_schema}/{site_slug}/{device.id}"
    
    logger.info(
        f"Iniciando provisionamento EMQX para Device {device.id} "
        f"(tenant={tenant_schema}, site={site_slug})"
    )
    
    try:
        # 1) Criar usuário no EMQX
        provisioner.create_user(creds)
        logger.info(f"✅ Usuário EMQX criado: {username}")
        
        # 2) Configurar ACL mínima
        provisioner.set_acl(
            creds,
            tenant=tenant_schema,
            site=site_slug,
            device=str(device.id)
        )
        logger.info(f"✅ ACL configurada para Device {device.id} (6 regras: 5 publish + 1 subscribe)")
        
        # 3) Atualizar Device no banco
        device.credentials_id = username
        device.topic_base = topic_base
        device.save(update_fields=['credentials_id', 'topic_base'])
        logger.info(f"✅ Device {device.id} atualizado com credentials_id e topic_base")
        
        # 4) Montar resposta com informações de conexão
        mqtt_info = {
            'mqtt': {
                'host': 'emqx.local',  # TODO: pegar de variável de ambiente
                'port': 1883,  # TODO: 8883 em produção (TLS)
                'client_id': client_id,
                'username': username,
                'password': password,  # ⚠️ SALVAR COM SEGURANÇA!
            },
            'topics': {
                'publish': [
                    f"{topic_base}/state",
                    f"{topic_base}/telem",
                    f"{topic_base}/event",
                    f"{topic_base}/alarm",
                    f"{topic_base}/ack",
                ],
                'subscribe': [
                    f"{topic_base}/cmd"
                ]
            },
            'lwt': {
                'topic': f"{topic_base}/state",
                'retain': True,
                'payload': '{"online": false, "ts": "<timestamp>"}',
                'qos': 1,
                'description': 'Last Will Testament - deve ser configurado pelo device ao conectar'
            }
        }
        
        logger.info(
            f"✅ Provisionamento EMQX concluído com sucesso para Device {device.id} "
            f"(username={username}, client_id={client_id})"
        )
        
        return mqtt_info
    
    except EmqxProvisioningError as e:
        logger.error(f"❌ Falha ao provisionar Device {device.id} no EMQX: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao provisionar Device {device.id}: {e}")
        raise EmqxProvisioningError(f"Erro inesperado durante provisionamento: {e}") from e


def deprovision_emqx_for_device(device: Device) -> None:
    """
    Remove credenciais MQTT do EMQX para um dispositivo.
    
    Remove:
        1. ACLs do usuário
        2. Usuário do sistema de autenticação
        3. Desconecta cliente MQTT se estiver conectado
    
    Args:
        device: Instância de Device a ser desprovisionada
    
    Raises:
        EmqxProvisioningError: Falha ao remover credenciais
    
    Comportamento:
        - Idempotente: não falha se usuário não existir
        - Limpa campos credentials_id e topic_base do Device
        - Logar operação para auditoria
    
    Exemplo:
        from devices.models import Device
        from devices.services import deprovision_emqx_for_device
        
        device = Device.objects.get(id='...')
        deprovision_emqx_for_device(device)
        
        # Ou via signal (ao deletar Device):
        @receiver(pre_delete, sender=Device)
        def device_pre_delete(sender, instance, **kwargs):
            if instance.credentials_id:
                deprovision_emqx_for_device(instance)
    """
    if not device.credentials_id:
        logger.warning(f"⚠️ Device {device.id} não possui credentials_id. Nada a desprovisar.")
        return
    
    provisioner = get_provisioner()
    
    logger.info(f"Iniciando desprovisionamento EMQX para Device {device.id} (username={device.credentials_id})")
    
    try:
        # Deletar usuário e ACLs do EMQX
        provisioner.delete_user(device.credentials_id)
        logger.info(f"✅ Usuário EMQX deletado: {device.credentials_id}")
        
        # Limpar campos do Device
        device.credentials_id = None
        device.topic_base = None
        device.save(update_fields=['credentials_id', 'topic_base'])
        logger.info(f"✅ Device {device.id} desprovisionado com sucesso")
    
    except EmqxProvisioningError as e:
        logger.error(f"❌ Falha ao desprovisar Device {device.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao desprovisar Device {device.id}: {e}")
        raise EmqxProvisioningError(f"Erro inesperado durante desprovisionamento: {e}") from e
