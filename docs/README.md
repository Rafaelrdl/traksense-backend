# Documentação - TrakSense Backend

> **🤖 AI ASSISTANTS:** When creating documentation files (.md), ALWAYS place them in the appropriate subfolder within `docs/`, NEVER in the project root. See the structure below and follow the naming conventions.

Diretório organizado contendo toda a documentação do projeto.

## 📁 Estrutura de Pastas

### 📋 fases/
Documentação de todas as fases de desenvolvimento do projeto.

**Arquivos:**
- `FASE_0_COMPLETA.md` - Fase 0: Infraestrutura base
- `FASE_0.7_*.md` - Fase 0.7: Preparação e planejamento
- `FASE_1_*.md` - Fase 1: Autenticação e autorização
- `FASE_2_*.md` - Fase 2: Catálogo de ativos
- `FASE_5_*.md` - Fase 5: Equipe e permissões
- `FASE_6_*.md` - Fase 6: Backend completo

### 🔨 implementacao/
Documentação detalhada de implementações específicas.

**Tópicos:**
- Auto-registro de sensores
- Auto-vinculação de tópicos
- Parsers de payload
- Vinculação de sensores

**Arquivos:**
- `IMPLEMENTACAO_AUTO_REGISTRO_SENSORES.md`
- `IMPLEMENTACAO_AUTO_VINCULACAO_TOPICO.md`
- `IMPLEMENTACAO_PARSERS_COMPLETA.md`
- `IMPLEMENTACAO_VINCULACAO_SENSORES.md`

### 📖 guias/
Guias práticos e tutoriais para operações específicas.

**Categorias:**
- **Configuração:** Webhook EMQX, criação manual de rules
- **Testes:** Alertas, fase 0.7, fase 5
- **Operações:** Publicação MQTT, vinculação de sensores, execução

**Arquivos:**
- `GUIA_CONFIGURAR_WEBHOOK_EMQX.md`
- `GUIA_CRIAR_RULE_MANUAL.md`
- `GUIA_EXECUCAO.md`
- `GUIA_PUBLICACAO_MQTTX.md`
- `GUIA_TESTE_ALERTAS.md`
- `GUIA_TESTES_FASE_0.7.md`
- `GUIA_TESTES_FASE_5.md`
- `GUIA_VINCULACAO_SENSORES.md`

### 🔌 emqx/
Documentação específica do EMQX (broker MQTT).

**Conteúdo:**
- Atualizações de connector
- Resumo de implementação
- Provisionamento
- Mudanças da versão 6
- Configuração para Windows

**Arquivos:**
- `EMQX_CONNECTOR_UPDATE.md`
- `EMQX_IMPLEMENTATION_SUMMARY.md`
- `EMQX_PROVISIONING.md`
- `EMQX_V6_CHANGES.md`
- `EMQX_WINDOWS.md`

### ✅ validacoes/
Relatórios de validação e testes finais.

**Tipos:**
- Validações de fases
- Validações EMQX multitenant
- Validações manuais
- Relatórios de testes

**Arquivos:**
- `VALIDACAO_FASE_0.md`
- `VALIDACAO_EMQX_MANUAL.md`
- `VALIDACAO_FINAL_EMQX_MULTITENANT.md`
- `RELATORIO_FINAL_VALIDACAO.md`
- `RELATORIO_TESTES_OPS_PANEL.md`

### 🐛 bugfixes/
Documentação de correções de bugs.

**Arquivos:**
- `BUGFIX_TELEMETRY_500_LABELS.md` - Correção de erro 500 em labels de telemetria
- `CORRECAO_EMQX_BODY.md` - Correção do body EMQX

### 📄 Arquivos na Raiz

- `AMBIENTE_PRONTO.md` - Guia de ambiente pronto
- `CHECKLIST_FASE_0.7.md` - Checklist da fase 0.7
- `COMANDOS_TESTE_EMQX.md` - Comandos para teste do EMQX
- `COMANDOS_WINDOWS.md` - Comandos específicos do Windows
- `CONTROL_CENTER_*.md` - Documentação do Control Center
- `DEFINITION_OF_DONE.md` - Definição de pronto
- `EXECUTADO_PROXIMOS_PASSOS.md` - Executado e próximos passos
- `PARSER_SYSTEM_GUIDE.md` - Guia do sistema de parsers
- `README_*.md` - READMEs específicos de funcionalidades
- `RESULTADO_EXECUCAO.md` - Resultados de execução
- `RESUMO_IMPLEMENTACAO_INGEST.md` - Resumo da implementação de ingest

## 🔍 Como Navegar

### Por Fase do Projeto
Acesse a pasta `fases/` para ver a documentação cronológica do desenvolvimento.

### Por Funcionalidade
- **EMQX/MQTT**: Veja `emqx/` e guias relacionados
- **Sensores**: Veja implementações e guias de vinculação
- **Testes**: Veja validações e guias de teste

### Por Tipo de Documento
- **Guias práticos**: `guias/`
- **Detalhes técnicos**: `implementacao/`
- **Resultados**: `validacoes/`
- **Correções**: `bugfixes/`

## 📝 Convenções

- **FASE_**: Documentação de fases do projeto
- **IMPLEMENTACAO_**: Detalhes técnicos de implementação
- **GUIA_**: Tutoriais passo-a-passo
- **VALIDACAO_**: Resultados de validação
- **RELATORIO_**: Relatórios formais
- **BUGFIX_**: Documentação de correções
- **CHECKLIST_**: Listas de verificação
