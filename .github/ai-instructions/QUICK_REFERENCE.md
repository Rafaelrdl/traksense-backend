# 🚀 Referência Rápida - Organização de Arquivos

> Para Desenvolvedores e Assistentes de IA

---

## 🎯 Regra de Ouro

**NUNCA crie arquivos .md ou .py na raiz do projeto!**

Use sempre: `docs/` ou `scripts/` + subpasta apropriada

---

## 📍 Onde Criar Cada Arquivo?

### Documentação (.md)

```
FASE_X_NOME.md           → docs/fases/
IMPLEMENTACAO_NOME.md    → docs/implementacao/
GUIA_NOME.md             → docs/guias/
EMQX_NOME.md             → docs/emqx/
VALIDACAO_NOME.md        → docs/validacoes/
RELATORIO_NOME.md        → docs/validacoes/
BUGFIX_NOME.md           → docs/bugfixes/
CORRECAO_NOME.md         → docs/bugfixes/
CHECKLIST_NOME.md        → docs/
COMANDOS_NOME.md         → docs/
README_NOME.md           → docs/
```

### Scripts Python (.py)

```
test_nome.py             → scripts/tests/
create_nome.py           → scripts/setup/
check_nome.py            → scripts/verification/
fix_nome.py              → scripts/maintenance/
cleanup_nome.py          → scripts/maintenance/
provision_nome.py        → scripts/utils/
publish_nome.py          → scripts/utils/
sync_nome.py             → scripts/utils/
debug_nome.py            → scripts/utils/
set_nome.py              → scripts/utils/
delete_nome.py           → scripts/utils/
verify_nome.py           → scripts/utils/
```

---

## ✅ Exceções (Permitidos na Raiz)

- `README.md`, `INDEX.md`, `NAVEGACAO.md`, `REORGANIZACAO.md`
- `AI_FILE_ORGANIZATION_WARNING.md`
- `manage.py`, `Makefile`, `requirements.txt`
- `.env`, `.env.example`, `.gitignore`
- `gunicorn.conf.py`, `celerybeat-schedule`

---

## 🔍 Como Decidir?

```
1. Qual é o prefixo do arquivo?
   └─ Consulte a tabela acima

2. É documentação ou script?
   └─ docs/ ou scripts/

3. É uma das exceções?
   └─ Se não, use subpasta

4. Crie com caminho completo!
   └─ docs/fases/FASE_7.md
```

---

## 📚 Documentação Completa

- **AI_FILE_ORGANIZATION_WARNING.md** - Regras visuais e detalhadas
- **.copilot-rules** - Resumo das regras
- **.github/copilot-instructions.md** - Instruções completas
- **.github/FILE_TEMPLATES.md** - Templates de arquivo
- **docs/FILE_PROTECTION_SYSTEM.md** - Sistema de proteção

---

## 🤖 Para Assistentes de IA

Antes de criar QUALQUER arquivo:

1. ✅ Ler `.copilot-rules`
2. ✅ Ler `AI_FILE_ORGANIZATION_WARNING.md`
3. ✅ Identificar prefixo do arquivo
4. ✅ Consultar tabela de localização
5. ✅ Criar com caminho COMPLETO

---

**Última atualização:** 30 de outubro de 2025
