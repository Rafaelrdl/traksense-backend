# ⚠️ AVISO PARA ASSISTENTES DE IA

## 🚨 NUNCA CRIE ARQUIVOS NA RAIZ DESTE DIRETÓRIO

Este projeto possui uma **estrutura organizacional rigorosa**. Todos os arquivos devem ser criados nas pastas apropriadas.

---

## 📍 Onde Criar Cada Tipo de Arquivo

### 📚 Arquivos de Documentação (.md)
**Localização:** `docs/` (NUNCA na raiz)

| Tipo de Documento | Pasta Correta |
|-------------------|---------------|
| Documentação de fases | `docs/fases/` |
| Documentação de implementação | `docs/implementacao/` |
| Guias e tutoriais | `docs/guias/` |
| Documentação EMQX | `docs/emqx/` |
| Validações e relatórios | `docs/validacoes/` |
| Correções de bugs | `docs/bugfixes/` |
| Outros documentos | `docs/` |

### 🔧 Scripts Python (.py)
**Localização:** `scripts/` (NUNCA na raiz)

| Tipo de Script | Pasta Correta |
|----------------|---------------|
| Scripts de teste | `scripts/tests/` |
| Scripts de setup/criação | `scripts/setup/` |
| Scripts de verificação | `scripts/verification/` |
| Scripts de manutenção | `scripts/maintenance/` |
| Scripts utilitários | `scripts/utils/` |

---

## ✅ Exceções (Únicos Arquivos Permitidos na Raiz)

- `README.md` - Documentação principal do projeto
- `INDEX.md` - Índice de navegação geral
- `NAVEGACAO.md` - Guia rápido de navegação
- `REORGANIZACAO.md` - Documentação da reorganização
- `manage.py` - Script de gerenciamento Django
- `gunicorn.conf.py` - Configuração do servidor
- `Makefile` - Comandos de build
- `requirements.txt` - Dependências Python
- `.env`, `.env.example` - Configurações de ambiente
- `.gitignore` - Configuração do Git
- `celerybeat-schedule` - Arquivo temporário do Celery

---

## 🎯 Convenções de Nomenclatura

A **nomenclatura define a localização**:

| Prefixo do Arquivo | Localização Correta |
|-------------------|---------------------|
| `FASE_*.md` | `docs/fases/` |
| `IMPLEMENTACAO_*.md` | `docs/implementacao/` |
| `GUIA_*.md` | `docs/guias/` |
| `EMQX_*.md` | `docs/emqx/` |
| `VALIDACAO_*.md` ou `RELATORIO_*.md` | `docs/validacoes/` |
| `BUGFIX_*.md` ou `CORRECAO_*.md` | `docs/bugfixes/` |
| `test_*.py` | `scripts/tests/` |
| `create_*.py` | `scripts/setup/` |
| `check_*.py` | `scripts/verification/` |
| `fix_*.py` ou `cleanup_*.py` | `scripts/maintenance/` |

---

## 📖 Documentação de Referência

Antes de criar qualquer arquivo, consulte:

1. **INDEX.md** - Índice completo do projeto
2. **docs/README.md** - Estrutura de documentação
3. **scripts/README.md** - Estrutura de scripts
4. **REORGANIZACAO.md** - Por que organizamos dessa forma
5. **.github/copilot-instructions.md** - Instruções completas

---

## 🤖 Checklist para IA antes de Criar Arquivos

- [ ] O arquivo é de documentação (.md)?
  - [ ] Identifiquei o prefixo correto (FASE_, GUIA_, etc)?
  - [ ] Escolhi a pasta correta em `docs/`?
  - [ ] **NÃO** vou criar na raiz?

- [ ] O arquivo é um script (.py)?
  - [ ] Identifiquei o prefixo correto (test_, create_, etc)?
  - [ ] Escolhi a pasta correta em `scripts/`?
  - [ ] **NÃO** vou criar na raiz?

- [ ] O arquivo é um dos permitidos na lista de exceções?
  - [ ] Se não, vou criar na pasta apropriada

---

## ❌ Exemplos de ERROS Comuns

```
❌ create_file("FASE_7_ANALYTICS.md")
✅ create_file("docs/fases/FASE_7_ANALYTICS.md")

❌ create_file("test_analytics.py")
✅ create_file("scripts/tests/test_analytics.py")

❌ create_file("GUIA_SETUP.md")
✅ create_file("docs/guias/GUIA_SETUP.md")

❌ create_file("check_data.py")
✅ create_file("scripts/verification/check_data.py")
```

---

## 🎓 Resumo

**Regra de Ouro:** Se você não tem certeza absoluta de que o arquivo pertence à raiz (e não está na lista de exceções), ele **NÃO** pertence à raiz.

**Sempre:**
1. Identifique o tipo de arquivo
2. Consulte as convenções de nomenclatura
3. Crie na pasta apropriada
4. **NUNCA** assuma que a raiz é o local correto

---

Este aviso existe porque o projeto foi **completamente reorganizado** em 30/10/2025, movendo 100 arquivos soltos para uma estrutura organizada. **Por favor, mantenha essa organização!**
