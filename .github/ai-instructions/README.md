# 🤖 AI Instructions - TrakSense Backend

> **CRITICAL:** All AI assistants (GitHub Copilot, ChatGPT, Claude, etc.) MUST read this folder before creating any files in this project.

---

## ⚠️ MANDATORY READING ORDER

**Before creating ANY file, read these documents in this order:**

1. **`.copilot-rules`** ⭐ - Quick rules summary (START HERE)
2. **`AI_FILE_ORGANIZATION_WARNING.md`** - Detailed visual guide
3. **`QUICK_REFERENCE.md`** - Quick lookup table

---

## 🎯 Purpose of This Folder

This folder contains **critical organizational rules** that prevent files from being created in the wrong locations.

### Why This Matters

In October 2025, this project underwent a **major reorganization**:
- **100 files** were moved from root to organized folders
- **`docs/` structure** created for documentation
- **`scripts/` structure** created for Python scripts

**We MUST maintain this organization!**

---

## 📋 Files in This Folder

### 1. `.copilot-rules`
**Purpose:** Quick reference rules for GitHub Copilot  
**When to read:** FIRST, before any file creation  
**Contents:**
- File naming conventions
- Location mappings
- Root directory whitelist

### 2. `AI_FILE_ORGANIZATION_WARNING.md`
**Purpose:** Comprehensive visual guide with examples  
**When to read:** When you need detailed guidance  
**Contents:**
- Complete tables of file types → locations
- Decision tree for placement
- Common mistakes and corrections
- Checklist before creating files

### 3. `QUICK_REFERENCE.md`
**Purpose:** Fast lookup table  
**When to read:** Quick validation of file location  
**Contents:**
- Concise prefix → location table
- Exception list
- Quick decision guide

---

## 🚨 Critical Rules Summary

### Rule #1: NEVER Create Files in Root
❌ **WRONG:** `c:\...\traksense-backend\FASE_7.md`  
✅ **CORRECT:** `c:\...\traksense-backend\docs\fases\FASE_7.md`

### Rule #2: Prefix Determines Location
- `FASE_*.md` → `docs/fases/`
- `IMPLEMENTACAO_*.md` → `docs/implementacao/`
- `GUIA_*.md` → `docs/guias/`
- `test_*.py` → `scripts/tests/`
- `create_*.py` → `scripts/setup/`
- `check_*.py` → `scripts/verification/`

### Rule #3: Root Whitelist Only
Only these files allowed in root:
- `README.md`, `INDEX.md`, `NAVEGACAO.md`, `REORGANIZACAO.md`
- `manage.py`, `Makefile`, `requirements.txt`
- `.env`, `.env.example`, `.gitignore`
- `gunicorn.conf.py`, `celerybeat-schedule`

---

## 🔄 AI Workflow

```
┌─────────────────────────────────────┐
│  AI wants to create a file          │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  1. Read .copilot-rules             │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  2. Identify file prefix            │
│     (FASE_, test_, GUIA_, etc)      │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  3. Lookup location in table        │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  4. Is it in root whitelist?        │
└───────────┬─────────────────────────┘
            │
            ├─── YES ──► Create in root
            │
            └─── NO ───► Create in subfolder
                         (docs/ or scripts/)
```

---

## 📚 Additional References

After reading this folder, consult:

### Project Documentation
- **`../../INDEX.md`** - Complete project index
- **`../../NAVEGACAO.md`** - Quick navigation guide
- **`../../REORGANIZACAO.md`** - Why we organized
- **`../../docs/README.md`** - Documentation structure
- **`../../scripts/README.md`** - Scripts structure

### AI-Specific Instructions
- **`../copilot-instructions.md`** - Full GitHub Copilot guide
- **`../FILE_TEMPLATES.md`** - Templates with correct paths
- **`../../docs/FILE_PROTECTION_SYSTEM.md`** - How the system works

---

## ✅ Compliance Checklist

Before creating ANY file, verify:

- [ ] I read `.copilot-rules`
- [ ] I identified the file prefix
- [ ] I checked the location table
- [ ] I verified it's NOT in root whitelist
- [ ] I'm using the FULL PATH (docs/fases/... or scripts/tests/...)
- [ ] I consulted the template if needed

---

## 🎓 Examples

### ✅ CORRECT File Creation

```python
# Documentation
create_file("docs/fases/FASE_7_ANALYTICS.md", content)
create_file("docs/guias/GUIA_ANALYTICS_SETUP.md", content)
create_file("docs/implementacao/IMPLEMENTACAO_DASHBOARD.md", content)

# Scripts
create_file("scripts/tests/test_analytics_api.py", content)
create_file("scripts/setup/create_analytics_data.py", content)
create_file("scripts/verification/check_analytics_config.py", content)
```

### ❌ WRONG File Creation

```python
# DON'T DO THIS!
create_file("FASE_7_ANALYTICS.md", content)  # ❌ Missing docs/fases/
create_file("test_analytics_api.py", content)  # ❌ Missing scripts/tests/
create_file("GUIA_ANALYTICS_SETUP.md", content)  # ❌ Missing docs/guias/
```

---

## 🛡️ Enforcement Layers

This folder is part of a **7-layer protection system**:

1. ✅ This README.md you're reading now
2. ✅ `.copilot-rules` - Quick rules
3. ✅ `AI_FILE_ORGANIZATION_WARNING.md` - Detailed guide
4. ✅ `QUICK_REFERENCE.md` - Fast lookup
5. ✅ `../copilot-instructions.md` - Section at top
6. ✅ `../FILE_TEMPLATES.md` - Templates with paths
7. ✅ READMEs in docs/ and scripts/ with warnings

**Multiple layers = Better compliance!**

---

## 🚀 Quick Start for AI

**First time in this project?**

1. Read `.copilot-rules` (2 minutes)
2. Read `AI_FILE_ORGANIZATION_WARNING.md` (5 minutes)
3. Bookmark `QUICK_REFERENCE.md` for future lookups
4. Consult templates in `../FILE_TEMPLATES.md` when creating files

**Creating a file now?**

1. What's the prefix? (FASE_, test_, etc)
2. Look it up in `QUICK_REFERENCE.md`
3. Use the full path
4. Done!

---

## 📞 When in Doubt

If you're unsure where a file belongs:

1. Check the prefix against `.copilot-rules`
2. If still unsure, read `AI_FILE_ORGANIZATION_WARNING.md`
3. If no prefix matches, use:
   - Documentation → `docs/`
   - Python script → `scripts/utils/`
4. **NEVER default to root!**

---

## 🎯 Success Metrics

This system is successful when:
- ✅ 0 new files created in root incorrectly
- ✅ All files follow naming conventions
- ✅ Project structure remains organized
- ✅ New developers can navigate easily

---

## 📊 Statistics

**Original reorganization (Oct 30, 2025):**
- 100 files moved from root
- 11 folders created
- 37 documentation files organized
- 63 script files organized

**Current protection:**
- 7 layers of enforcement
- 4 instruction files
- 100% coverage of file types

---

**🤖 Remember:** Your primary job is to maintain this organization. Every file in the right place = Better project for everyone!

---

**Last updated:** 30 de outubro de 2025  
**Maintained by:** TrakSense Development Team  
**Status:** Active and enforced
