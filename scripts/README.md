# Scripts - TrakSense Backend

> **🤖 AI ASSISTANTS:** When creating Python scripts (.py), ALWAYS place them in the appropriate subfolder within `scripts/`, NEVER in the project root. See the structure below and follow the naming conventions.

Diretório organizado contendo todos os scripts utilitários do projeto.

## 📁 Estrutura de Pastas

### 🧪 tests/
Scripts de teste para validar funcionalidades do sistema.
- `test_*.py` - Scripts de testes diversos (API, autenticação, telemetria, etc)

**Exemplos:**
- `test_auth_fase1.py` - Testes de autenticação
- `test_telemetry_api_endpoint.py` - Testes de API de telemetria
- `test_team_permissions.py` - Testes de permissões de equipe

### ⚙️ setup/
Scripts para criar e configurar recursos no sistema.
- `create_*.py` - Scripts de criação de recursos

**Exemplos:**
- `create_admin_umc.py` - Criar admin UMC
- `create_tenant_umc_localhost.py` - Criar tenant local
- `create_demo_team.py` - Criar equipe demo
- `create_alerts_example.py` - Criar alertas de exemplo

### 🔍 verification/
Scripts para verificar estado e configurações do sistema.
- `check_*.py` - Scripts de verificação

**Exemplos:**
- `check_assets_tenant.py` - Verificar assets de tenant
- `check_sensor_status.py` - Verificar status de sensores
- `check_telemetry_data.py` - Verificar dados de telemetria
- `check_tenant_domain.py` - Verificar domínio de tenant

### 🔧 maintenance/
Scripts para manutenção, correção e limpeza do sistema.
- `fix_*.py` - Scripts de correção
- `cleanup_*.py` - Scripts de limpeza

**Exemplos:**
- `fix_gerente_role.py` - Corrigir role de gerente
- `fix_umc_domains.py` - Corrigir domínios UMC
- `cleanup_tenants.py` - Limpar tenants
- `cleanup_test_sites.py` - Limpar sites de teste

### 🛠️ utils/
Scripts utilitários diversos.
- `provision_*.py` - Scripts de provisionamento
- `publish_*.py` - Scripts de publicação MQTT
- `sync_*.py` - Scripts de sincronização
- `verify_*.py` - Scripts de verificação
- `delete_*.py` - Scripts de deleção
- `debug_*.py` - Scripts de debug
- `set_*.py` - Scripts de configuração

**Exemplos:**
- `provision_sensors.py` - Provisionar sensores
- `publish_test_telemetry.py` - Publicar telemetria de teste
- `sync_users_to_tenant.py` - Sincronizar usuários
- `debug_permission.py` - Debug de permissões
- `set_admin_password.py` - Definir senha admin

## 🚀 Como Usar

### Executar Testes
```bash
python scripts/tests/test_auth_fase1.py
```

### Setup Inicial
```bash
python scripts/setup/create_admin_umc.py
python scripts/setup/create_tenant_umc_localhost.py
```

### Verificação de Sistema
```bash
python scripts/verification/check_sensor_status.py
python scripts/verification/check_telemetry_data.py
```

### Manutenção
```bash
python scripts/maintenance/cleanup_tenants.py
python scripts/maintenance/fix_gerente_role.py
```

## 📝 Notas

- Todos os scripts assumem que o ambiente virtual está ativado
- Verifique as variáveis de ambiente necessárias em cada script
- Scripts de teste podem requerer dados específicos no banco
- Scripts de setup devem ser executados na ordem correta para inicialização
