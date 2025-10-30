# 📚 Índice Geral - TrakSense Backend

Este documento serve como guia de navegação para toda a estrutura organizada do projeto.

## 📂 Estrutura do Projeto

```
traksense-backend/
├── 📁 docs/               # Documentação completa do projeto (37 arquivos)
│   ├── 📁 fases/         # Documentação de fases (13 arquivos)
│   ├── 📁 implementacao/ # Implementações técnicas (4 arquivos)
│   ├── 📁 guias/         # Guias práticos (8 arquivos)
│   ├── 📁 emqx/          # Docs EMQX/MQTT (5 arquivos)
│   ├── 📁 validacoes/    # Validações e relatórios (5 arquivos)
│   ├── 📁 bugfixes/      # Correções documentadas (2 arquivos)
│   └── README.md         # Índice de documentação
│
├── 📁 scripts/           # Scripts utilitários (63 arquivos)
│   ├── 📁 tests/         # Scripts de teste (29 arquivos)
│   ├── 📁 setup/         # Scripts de configuração (12 arquivos)
│   ├── 📁 verification/  # Scripts de verificação (9 arquivos)
│   ├── 📁 utils/         # Scripts diversos (9 arquivos)
│   ├── 📁 maintenance/   # Scripts de manutenção (4 arquivos)
│   └── README.md         # Índice de scripts
│
├── 📁 apps/              # Aplicações Django
├── 📁 config/            # Configurações do projeto
├── 📁 docker/            # Docker e containers
├── 📁 templates/         # Templates HTML
└── 📁 staticfiles/       # Arquivos estáticos
```

## 🚀 Quick Start

### 1. Configuração Inicial
Consulte os guias de setup:
- `docs/guias/GUIA_EXECUCAO.md` - Como executar o projeto
- `docs/AMBIENTE_PRONTO.md` - Preparação do ambiente

### 2. Desenvolvimento por Fase
Acompanhe a evolução do projeto:
- `docs/fases/FASE_0_COMPLETA.md` - Infraestrutura base
- `docs/fases/FASE_1_AUTENTICACAO_COMPLETA.md` - Autenticação
- `docs/fases/FASE_2_CATALOGO_ATIVOS.md` - Catálogo de ativos
- `docs/fases/FASE_5_RESUMO_EXECUTIVO.md` - Equipe e permissões
- `docs/fases/FASE_6_BACKEND_COMPLETO.md` - Backend completo

### 3. Testes
Execute scripts de teste organizados:
```bash
# Teste de autenticação
python scripts/tests/test_auth_fase1.py

# Teste de telemetria
python scripts/tests/test_telemetry_api_endpoint.py

# Teste de permissões
python scripts/tests/test_team_permissions.py
```

### 4. Setup de Ambiente
Scripts para configurar recursos:
```bash
# Criar admin
python scripts/setup/create_admin_umc.py

# Criar tenant
python scripts/setup/create_tenant_umc_localhost.py

# Criar equipe demo
python scripts/setup/create_demo_team.py
```

## 🤖 Para Assistentes de IA

**⚠️ LEIA ANTES DE CRIAR QUALQUER ARQUIVO:**

Consulte a pasta **`.github/ai-instructions/`** que contém:

1. **`.copilot-rules`** ⭐ - COMECE AQUI (regras rápidas)
2. **`AI_FILE_ORGANIZATION_WARNING.md`** - Guia visual detalhado
3. **`QUICK_REFERENCE.md`** - Tabela de consulta rápida
4. **`README.md`** - Visão geral e workflow

**Também consulte:**
- **`.github/copilot-instructions.md`** - Instruções completas (seção no topo)
- **`.github/FILE_TEMPLATES.md`** - Templates para novos arquivos

**Regra Principal:** NUNCA crie arquivos .md ou .py na raiz. Use `docs/` ou `scripts/`.

---

## 📖 Documentação por Tópico

### 🔐 Autenticação e Autorização
- `docs/fases/FASE_1_AUTENTICACAO_COMPLETA.md`
- `docs/fases/FASE_1_VALIDACAO_FINAL.md`
- `scripts/tests/test_auth_fase1.py`
- `scripts/tests/test_tenant_login.py`

### 🏢 Multi-tenancy
- `docs/fases/FASE_0_COMPLETA.md`
- `docs/guias/GUIA_EXECUCAO.md`
- `scripts/setup/create_tenant_umc_localhost.py`
- `scripts/verification/check_tenant_domain.py`

### 📡 MQTT e EMQX
- `docs/emqx/EMQX_IMPLEMENTATION_SUMMARY.md`
- `docs/emqx/EMQX_PROVISIONING.md`
- `docs/emqx/EMQX_V6_CHANGES.md`
- `docs/guias/GUIA_CONFIGURAR_WEBHOOK_EMQX.md`
- `docs/guias/GUIA_PUBLICACAO_MQTTX.md`
- `docs/COMANDOS_TESTE_EMQX.md`
- `scripts/utils/publish_test_telemetry.py`
- `scripts/tests/test_mqtt_publish.py`

### 📊 Telemetria
- `docs/implementacao/IMPLEMENTACAO_PARSERS_COMPLETA.md`
- `docs/PARSER_SYSTEM_GUIDE.md`
- `docs/RESUMO_IMPLEMENTACAO_INGEST.md`
- `scripts/tests/test_telemetry_api_endpoint.py`
- `scripts/tests/test_telemetry_data_direct.py`
- `scripts/verification/check_telemetry_data.py`

### 🔔 Alertas
- `docs/guias/GUIA_TESTE_ALERTAS.md`
- `scripts/setup/create_alerts_example.py`
- `scripts/tests/test_alerts_integration.py`

### 🔧 Sensores
- `docs/implementacao/IMPLEMENTACAO_AUTO_REGISTRO_SENSORES.md`
- `docs/implementacao/IMPLEMENTACAO_VINCULACAO_SENSORES.md`
- `docs/guias/GUIA_VINCULACAO_SENSORES.md`
- `docs/README_VINCULACAO_SENSORES.md`
- `scripts/utils/provision_sensors.py`
- `scripts/verification/check_sensor_status.py`

### 👥 Equipes e Permissões
- `docs/fases/FASE_5_RESUMO_EXECUTIVO.md`
- `docs/fases/FASE_5_EQUIPE_PERMISSOES.md`
- `docs/guias/GUIA_TESTES_FASE_5.md`
- `scripts/setup/create_demo_team.py`
- `scripts/tests/test_team_permissions.py`

### 🏗️ Assets
- `docs/fases/FASE_2_CATALOGO_ATIVOS.md`
- `scripts/tests/test_assets_api.py`
- `scripts/verification/check_assets_tenant.py`

## 🐛 Troubleshooting

### Correções Conhecidas
- `docs/bugfixes/BUGFIX_TELEMETRY_500_LABELS.md`
- `docs/bugfixes/CORRECAO_EMQX_BODY.md`

### Scripts de Manutenção
```bash
# Corrigir roles
python scripts/maintenance/fix_gerente_role.py

# Limpar tenants de teste
python scripts/maintenance/cleanup_tenants.py

# Corrigir domínios
python scripts/maintenance/fix_umc_domains.py
```

### Verificação de Sistema
```bash
# Verificar sensores
python scripts/verification/check_sensor_status.py

# Verificar telemetria
python scripts/verification/check_telemetry_data.py

# Verificar assets
python scripts/verification/check_assets_tenant.py
```

## 📝 Convenções de Nomenclatura

### Arquivos de Documentação (.md)
- **FASE_**: Documentação de fases do projeto
- **IMPLEMENTACAO_**: Detalhes técnicos de implementação
- **GUIA_**: Tutoriais passo-a-passo
- **VALIDACAO_**: Resultados de validação
- **RELATORIO_**: Relatórios formais
- **BUGFIX_**: Documentação de correções
- **CHECKLIST_**: Listas de verificação
- **COMANDOS_**: Comandos úteis

### Scripts Python (.py)
- **test_**: Scripts de teste
- **create_**: Scripts de criação de recursos
- **check_**: Scripts de verificação
- **fix_**: Scripts de correção
- **cleanup_**: Scripts de limpeza
- **provision_**: Scripts de provisionamento
- **publish_**: Scripts de publicação MQTT
- **sync_**: Scripts de sincronização
- **debug_**: Scripts de debug

## 🔗 Links Rápidos

### Documentação Principal
- [README Principal](README.md)
- [Documentação Completa](docs/README.md)
- [Scripts](scripts/README.md)

### Definições
- [Definition of Done](docs/DEFINITION_OF_DONE.md)
- [Parser System Guide](docs/PARSER_SYSTEM_GUIDE.md)

### READMEs Específicos
- [README Fase 0.7](docs/README_FASE_0.7.md)
- [README Vinculação Sensores](docs/README_VINCULACAO_SENSORES.md)

## 📊 Estatísticas

- **Total de Documentos**: 37 arquivos .md organizados
- **Total de Scripts**: 63 arquivos .py organizados
- **Fases Documentadas**: 6 fases principais
- **Scripts de Teste**: 29 scripts
- **Scripts de Setup**: 12 scripts
- **Guias Práticos**: 8 guias

## 🎯 Próximos Passos

1. Consulte o índice apropriado:
   - Para documentação: `docs/README.md`
   - Para scripts: `scripts/README.md`

2. Navegue por fase do projeto em `docs/fases/`

3. Execute testes conforme necessário em `scripts/tests/`

4. Configure ambiente usando `scripts/setup/`

---

**Última atualização**: 30 de outubro de 2025  
**Versão**: 1.0  
**Mantido por**: Equipe TrakSense
