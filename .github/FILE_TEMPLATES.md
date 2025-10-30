# File Templates - TrakSense Backend

Este arquivo contém templates que a IA deve usar ao criar novos arquivos.

---

## 📚 Template para Documentação de Fase

**Nome do arquivo:** `docs/fases/FASE_X_NOME.md`

```markdown
# Fase X - Nome da Fase

**Data de início:** DD/MM/AAAA  
**Status:** Em progresso | Concluído  
**Responsável:** Nome

## 🎯 Objetivos

- Objetivo 1
- Objetivo 2
- Objetivo 3

## 📋 Escopo

### Funcionalidades
- Funcionalidade 1
- Funcionalidade 2

### Fora do Escopo
- Item fora do escopo

## 🏗️ Arquitetura

[Descrição da arquitetura]

## 📝 Implementação

### Backend
[Detalhes de implementação]

### Frontend
[Detalhes de implementação]

## 🧪 Testes

[Estratégia de testes]

## ✅ Definition of Done

- [ ] Todos os endpoints implementados
- [ ] Testes unitários passando
- [ ] Documentação atualizada
- [ ] Code review aprovado
- [ ] Deploy em staging

## 📊 Resultados

[Resultados obtidos]

## 🔗 Links Relacionados

- [Documento relacionado 1]
- [Documento relacionado 2]

---

**Última atualização:** DD/MM/AAAA
```

---

## 🔨 Template para Documentação de Implementação

**Nome do arquivo:** `docs/implementacao/IMPLEMENTACAO_NOME.md`

```markdown
# Implementação - Nome da Funcionalidade

**Data:** DD/MM/AAAA  
**Versão:** 1.0  
**Status:** Implementado | Em progresso

## 📌 Resumo

[Breve descrição da implementação]

## 🎯 Objetivo

[O que esta implementação resolve]

## 🏗️ Arquitetura

### Componentes
- Componente 1
- Componente 2

### Fluxo de Dados
[Descrição do fluxo]

## 💻 Código

### Models
```python
# Exemplo de modelo
```

### Views/ViewSets
```python
# Exemplo de view
```

### Serializers
```python
# Exemplo de serializer
```

## 🔧 Configuração

[Passos de configuração necessários]

## 🧪 Testes

### Teste Manual
```bash
# Comandos para testar
```

### Teste Automatizado
```python
# Exemplo de teste
```

## 📊 Performance

[Considerações de performance]

## 🐛 Troubleshooting

### Problema 1
**Sintoma:** [descrição]  
**Solução:** [solução]

## 🔗 Referências

- [Link 1]
- [Link 2]

---

**Última atualização:** DD/MM/AAAA
```

---

## 📖 Template para Guias

**Nome do arquivo:** `docs/guias/GUIA_NOME.md`

```markdown
# Guia - Nome do Guia

**Dificuldade:** Iniciante | Intermediário | Avançado  
**Tempo estimado:** X minutos  
**Última atualização:** DD/MM/AAAA

## 🎯 Objetivo

[O que este guia ensina]

## ⚙️ Pré-requisitos

- Pré-requisito 1
- Pré-requisito 2

## 📋 Passo a Passo

### 1. Primeiro Passo

[Descrição]

```bash
# Comando
```

### 2. Segundo Passo

[Descrição]

```bash
# Comando
```

### 3. Terceiro Passo

[Descrição]

## ✅ Verificação

Como verificar se tudo está funcionando:

```bash
# Comando de verificação
```

**Resultado esperado:**
```
[Saída esperada]
```

## 🐛 Problemas Comuns

### Erro 1
**Mensagem:** [mensagem de erro]  
**Causa:** [causa]  
**Solução:** [solução]

## 🔗 Próximos Passos

- [Guia relacionado 1]
- [Guia relacionado 2]

---

**Dúvidas?** Consulte [documento relacionado]
```

---

## 🧪 Template para Script de Teste

**Nome do arquivo:** `scripts/tests/test_nome.py`

```python
"""
Test: Nome do Teste

Descrição: O que este teste valida
Autor: Nome
Data: DD/MM/AAAA
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

# Imports
from apps.nome_app.models import Modelo


def test_funcionalidade():
    """Testa a funcionalidade X"""
    print("🧪 Iniciando teste...")
    
    try:
        # Lógica do teste
        resultado = funcao_teste()
        
        assert resultado == esperado, f"Esperado {esperado}, obtido {resultado}"
        
        print("✅ Teste passou!")
        return True
        
    except Exception as e:
        print(f"❌ Teste falhou: {str(e)}")
        return False


if __name__ == '__main__':
    print(f"\n{'='*60}")
    print("Test: Nome do Teste")
    print(f"{'='*60}\n")
    
    sucesso = test_funcionalidade()
    
    print(f"\n{'='*60}")
    print(f"Resultado: {'✅ SUCESSO' if sucesso else '❌ FALHA'}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if sucesso else 1)
```

---

## ⚙️ Template para Script de Setup

**Nome do arquivo:** `scripts/setup/create_nome.py`

```python
"""
Setup: Criar Nome

Descrição: Script para criar/configurar recurso X
Autor: Nome
Data: DD/MM/AAAA

Uso:
    python scripts/setup/create_nome.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

# Imports
from apps.nome_app.models import Modelo


def criar_recurso():
    """Cria o recurso X"""
    print("🔧 Criando recurso...")
    
    try:
        # Lógica de criação
        recurso = Modelo.objects.create(
            campo1='valor1',
            campo2='valor2'
        )
        
        print(f"✅ Recurso criado: {recurso}")
        return recurso
        
    except Exception as e:
        print(f"❌ Erro ao criar recurso: {str(e)}")
        raise


def main():
    """Função principal"""
    print(f"\n{'='*60}")
    print("Setup: Criar Nome")
    print(f"{'='*60}\n")
    
    # Confirmar ação
    confirmar = input("Deseja criar o recurso? (s/n): ")
    if confirmar.lower() != 's':
        print("❌ Operação cancelada")
        return
    
    # Executar
    recurso = criar_recurso()
    
    print(f"\n{'='*60}")
    print("✅ Setup concluído com sucesso!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
```

---

## 🔍 Template para Script de Verificação

**Nome do arquivo:** `scripts/verification/check_nome.py`

```python
"""
Verification: Verificar Nome

Descrição: Verifica estado/configuração do recurso X
Autor: Nome
Data: DD/MM/AAAA

Uso:
    python scripts/verification/check_nome.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

# Imports
from apps.nome_app.models import Modelo


def verificar_recurso():
    """Verifica o recurso X"""
    print("🔍 Verificando recurso...")
    
    try:
        # Lógica de verificação
        recursos = Modelo.objects.all()
        
        print(f"\n📊 Recursos encontrados: {recursos.count()}")
        
        for recurso in recursos:
            print(f"  - {recurso}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {str(e)}")
        return False


def main():
    """Função principal"""
    print(f"\n{'='*60}")
    print("Verification: Verificar Nome")
    print(f"{'='*60}\n")
    
    sucesso = verificar_recurso()
    
    print(f"\n{'='*60}")
    print(f"Status: {'✅ OK' if sucesso else '❌ FALHA'}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if sucesso else 1)


if __name__ == '__main__':
    main()
```

---

## 🚨 LEMBRETE IMPORTANTE

Ao usar estes templates:

1. **SEMPRE** crie o arquivo na pasta correta:
   - Documentação → `docs/` (subpastas apropriadas)
   - Scripts → `scripts/` (subpastas apropriadas)

2. **NUNCA** crie arquivos na raiz do projeto

3. **SEMPRE** siga as convenções de nomenclatura

4. Consulte:
   - `INDEX.md` - Navegação completa
   - `docs/README.md` - Estrutura de docs
   - `scripts/README.md` - Estrutura de scripts
