"""
Management Command: provision_emqx

Provisiona credenciais MQTT no EMQX para um dispositivo via CLI.

Uso:
    # Provisionar device específico:
    python manage.py tenant_command provision_emqx <device_id> <site_slug> --schema=test_alpha
    
    # Exibir ajuda:
    python manage.py tenant_command provision_emqx --help --schema=test_alpha

Exemplo:
    python manage.py tenant_command provision_emqx \\
        8b848ad7-7f07-4479-9ecd-32f0f68ffca5 \\
        factory-sp \\
        --schema=test_alpha
    
    # Saída esperada:
    ✅ Device provisionado com sucesso!
    
    MQTT Connection Info:
      Host: emqx.local
      Port: 1883
      ClientID: ts-1a2b3c4d-9f8e7d6c-a1b2c3d4
      Username: t:1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6:d:9f8e7d6c-5b4a-3210-fedc-ba0987654321
      Password: Xy9Kp2Lm4Nq6Rs8Tv0Uw  ⚠️ SALVE COM SEGURANÇA!
    
    Topics (Publish):
      - traksense/1a2b.../factory-sp/9f8e.../state
      - traksense/1a2b.../factory-sp/9f8e.../telem
      - traksense/1a2b.../factory-sp/9f8e.../event
      - traksense/1a2b.../factory-sp/9f8e.../alarm
      - traksense/1a2b.../factory-sp/9f8e.../ack
    
    Topics (Subscribe):
      - traksense/1a2b.../factory-sp/9f8e.../cmd
    
    LWT (Last Will Testament):
      Topic: traksense/1a2b.../factory-sp/9f8e.../state
      Retain: True
      QoS: 1
      Payload: {"online": false, "ts": "<timestamp>"}
      
      ⚠️ O device deve configurar LWT ao conectar!

Segurança:
    ⚠️ CRÍTICO: A senha exibida deve ser salva com segurança!
        - Usar secrets manager (AWS Secrets, Azure KeyVault)
        - OU exibir apenas 1x ao operador
        - NUNCA armazenar em plain-text no banco

Autor: TrakSense Team
Data: 2025-10-07 (Fase 3)
"""

import json
from django.core.management.base import BaseCommand, CommandError
from apps.devices.models import Device
from apps.devices.services import provision_emqx_for_device
from apps.devices.provisioning.emqx import EmqxProvisioningError


class Command(BaseCommand):
    """
    Management command para provisionar credenciais MQTT no EMQX.
    """
    
    help = (
        "Provisiona credenciais MQTT no EMQX para um dispositivo IoT.\n\n"
        "Uso: python manage.py tenant_command provision_emqx <device_id> <site_slug> --schema=<tenant>\n\n"
        "Exemplo:\n"
        "  python manage.py tenant_command provision_emqx \\\n"
        "      8b848ad7-7f07-4479-9ecd-32f0f68ffca5 \\\n"
        "      factory-sp \\\n"
        "      --schema=test_alpha"
    )
    
    def add_arguments(self, parser):
        """
        Define argumentos do comando.
        
        Args:
            parser: ArgumentParser do Django
        """
        # Argumentos posicionais
        parser.add_argument(
            'device_id',
            type=str,
            help='UUID do Device a ser provisionado'
        )
        
        parser.add_argument(
            'site_slug',
            type=str,
            help='Slug do site (para montar topic_base, ex: factory-sp, sala-a)'
        )
        
        # Argumentos opcionais
        parser.add_argument(
            '--password-length',
            type=int,
            default=20,
            help='Comprimento da senha gerada (mínimo 16, padrão 20)'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Exibir saída em formato JSON (para scripting)'
        )
    
    def handle(self, *args, **options):
        """
        Executa o comando de provisionamento.
        
        Args:
            *args: Argumentos posicionais
            **options: Argumentos opcionais
        
        Raises:
            CommandError: Falha no provisionamento
        """
        device_id = options['device_id']
        site_slug = options['site_slug']
        password_length = options['password_length']
        json_output = options['json']
        
        # Buscar Device
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            raise CommandError(f"❌ Device não encontrado: {device_id}")
        
        from django.db import connection
        tenant_schema = connection.schema_name
        
        self.stdout.write(
            f"Provisionando Device {device.id} ({device.name}) no EMQX..."
        )
        self.stdout.write(f"  Tenant: {tenant_schema}")
        self.stdout.write(f"  Template: {device.template.code} v{device.template.version}")
        self.stdout.write(f"  Site: {site_slug}")
        self.stdout.write("")
        
        # Provisionar
        try:
            mqtt_info = provision_emqx_for_device(
                device=device,
                site_slug=site_slug,
                password_length=password_length
            )
        except EmqxProvisioningError as e:
            raise CommandError(f"❌ Falha ao provisionar: {e}")
        except Exception as e:
            raise CommandError(f"❌ Erro inesperado: {e}")
        
        # Exibir resultado
        if json_output:
            # Formato JSON (para scripting)
            self.stdout.write(json.dumps(mqtt_info, indent=2))
        else:
            # Formato humano (para terminal)
            self._print_human_output(mqtt_info, device)
    
    def _print_human_output(self, mqtt_info: dict, device: Device):
        """
        Exibe saída formatada para humanos.
        
        Args:
            mqtt_info: Dicionário com informações de conexão MQTT
            device: Instância do Device provisionado
        """
        self.stdout.write(self.style.SUCCESS("✅ Device provisionado com sucesso!\n"))
        
        # Informações de conexão MQTT
        self.stdout.write(self.style.NOTICE("MQTT Connection Info:"))
        mqtt = mqtt_info['mqtt']
        self.stdout.write(f"  Host:     {mqtt['host']}")
        self.stdout.write(f"  Port:     {mqtt['port']}")
        self.stdout.write(f"  ClientID: {mqtt['client_id']}")
        self.stdout.write(f"  Username: {mqtt['username']}")
        self.stdout.write(self.style.WARNING(f"  Password: {mqtt['password']}  ⚠️ SALVE COM SEGURANÇA!"))
        self.stdout.write("")
        
        # Tópicos de publish
        self.stdout.write(self.style.NOTICE("Topics (Publish):"))
        for topic in mqtt_info['topics']['publish']:
            self.stdout.write(f"  - {topic}")
        self.stdout.write("")
        
        # Tópicos de subscribe
        self.stdout.write(self.style.NOTICE("Topics (Subscribe):"))
        for topic in mqtt_info['topics']['subscribe']:
            self.stdout.write(f"  - {topic}")
        self.stdout.write("")
        
        # Last Will Testament
        self.stdout.write(self.style.NOTICE("LWT (Last Will Testament):"))
        lwt = mqtt_info['lwt']
        self.stdout.write(f"  Topic:   {lwt['topic']}")
        self.stdout.write(f"  Retain:  {lwt['retain']}")
        self.stdout.write(f"  QoS:     {lwt['qos']}")
        self.stdout.write(f"  Payload: {lwt['payload']}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  ⚠️ O device deve configurar LWT ao conectar!"))
        self.stdout.write("")
        
        # Avisos de segurança
        self.stdout.write(self.style.ERROR("⚠️ SEGURANÇA:"))
        self.stdout.write("  - Salve a senha em um secrets manager (AWS Secrets, Azure KeyVault)")
        self.stdout.write("  - OU exiba apenas 1x ao operador e nunca mais recupere")
        self.stdout.write("  - NUNCA armazene em plain-text no banco de dados")
        self.stdout.write("  - Em produção, considere rotação automática de senhas")
        self.stdout.write("")
        
        # Próximos passos
        self.stdout.write(self.style.SUCCESS("Próximos passos:"))
        self.stdout.write("  1. Configure o device IoT com as credenciais acima")
        self.stdout.write("  2. Configure o LWT no device (topic state com retain=true)")
        self.stdout.write("  3. Teste a conexão MQTT")
        self.stdout.write("  4. Verifique os logs do EMQX (docker compose logs -f emqx)")
        self.stdout.write("  5. Valide que o device só acessa seus próprios tópicos (ACL)")
