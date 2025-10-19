# 🔐 FASE 1: Autenticação e Usuários - IMPLEMENTAÇÃO COMPLETA

## ✅ Status: CONCLUÍDA

**Data:** 18 de outubro de 2025

---

## 📋 Resumo das Implementações

### 1. ✅ Dependências Instaladas
- `djangorestframework-simplejwt==5.3.1` - JWT Authentication
- `Pillow==10.2.0` - Image processing para avatares
- `rest_framework_simplejwt.token_blacklist` - Token blacklist para logout

### 2. ✅ Modelo User Expandido
**Arquivo:** `apps/accounts/models.py`

**Novos campos:**
- `email` - Email único e obrigatório
- `avatar` - URL do avatar no MinIO
- `phone` - Telefone (opcional)
- `bio` - Biografia (opcional)
- `timezone` - Fuso horário (default: America/Sao_Paulo)
- `language` - Idioma (default: pt-br)
- `email_verified` - Status de verificação de email
- `last_login_ip` - IP do último login
- `created_at` - Data de criação
- `updated_at` - Data de atualização

**Propriedades:**
- `full_name` - Nome completo do usuário
- `initials` - Iniciais para avatar fallback

### 3. ✅ Serializers Implementados
**Arquivo:** `apps/accounts/serializers.py`

- **UserSerializer** - Serialização completa do usuário
- **UserUpdateSerializer** - Atualização de perfil
- **RegisterSerializer** - Registro de novos usuários
- **LoginSerializer** - Login com email ou username
- **CustomTokenObtainPairSerializer** - JWT com dados do usuário
- **ChangePasswordSerializer** - Alteração de senha

### 4. ✅ Views Implementadas
**Arquivo:** `apps/accounts/views.py`

- **RegisterView** - Registro de usuários
- **LoginView** - Login com JWT e cookies HttpOnly
- **LogoutView** - Logout com blacklist de tokens
- **MeView** - GET/PATCH perfil do usuário
- **ChangePasswordView** - Alteração de senha
- **AvatarUploadView** - Upload/Delete de avatar no MinIO

### 5. ✅ Configurações JWT
**Arquivo:** `config/settings/base.py`

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

**CORS configurado para cookies:**
```python
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
```

### 6. ✅ Storage MinIO
**Arquivo:** `apps/common/storage.py`

- `get_minio_client()` - Cliente MinIO configurado
- `ensure_bucket_exists()` - Criação automática de buckets

---

## 🔗 Endpoints Disponíveis

### Base URL (Tenant)
```
http://[tenant-domain]/api/
```

### Autenticação

#### 1. Registro
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response 201:**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "initials": "JD",
    "avatar": null,
    "phone": null,
    "bio": null,
    "timezone": "America/Sao_Paulo",
    "language": "pt-br",
    "email_verified": false,
    "is_active": true,
    "is_staff": false,
    "date_joined": "2025-10-18T20:00:00Z",
    "created_at": "2025-10-18T20:00:00Z"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Usuário registrado com sucesso!"
}
```

#### 2. Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username_or_email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response 200:**
```json
{
  "user": { /* dados do usuário */ },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Login realizado com sucesso!"
}
```

**Cookies HttpOnly definidos:**
- `access_token` - válido por 1 hora
- `refresh_token` - válido por 7 dias

#### 3. Logout
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 200:**
```json
{
  "message": "Logout realizado com sucesso!"
}
```

#### 4. Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Perfil do Usuário

#### 5. Obter Perfil Atual
```http
GET /api/users/me/
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "initials": "JD",
  "avatar": "http://minio:9000/files/avatars/1/abc123.jpg",
  "phone": "+55 11 98765-4321",
  "bio": "Desenvolvedor Full Stack",
  "timezone": "America/Sao_Paulo",
  "language": "pt-br",
  "email_verified": false,
  "is_active": true,
  "is_staff": false,
  "date_joined": "2025-10-18T20:00:00Z",
  "last_login": "2025-10-18T20:30:00Z",
  "created_at": "2025-10-18T20:00:00Z",
  "updated_at": "2025-10-18T20:30:00Z"
}
```

#### 6. Atualizar Perfil
```http
PATCH /api/users/me/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Jonathan",
  "phone": "+55 11 98765-4321",
  "bio": "Desenvolvedor Full Stack apaixonado por tecnologia",
  "timezone": "America/Sao_Paulo",
  "language": "pt-br"
}
```

**Response 200:**
```json
{
  "user": { /* dados atualizados */ },
  "message": "Perfil atualizado com sucesso!"
}
```

#### 7. Upload de Avatar
```http
POST /api/users/me/avatar/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

avatar=<arquivo.jpg>
```

**Response 200:**
```json
{
  "avatar": "http://minio:9000/files/avatars/1/uuid.jpg",
  "message": "Avatar atualizado com sucesso!"
}
```

**Validações:**
- Tipos permitidos: JPG, PNG, GIF, WebP
- Tamanho máximo: 5MB
- Armazenamento: MinIO bucket `files`

#### 8. Remover Avatar
```http
DELETE /api/users/me/avatar/
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "message": "Avatar removido com sucesso!"
}
```

#### 9. Alterar Senha
```http
POST /api/users/me/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password_confirm": "NewPass123!"
}
```

**Response 200:**
```json
{
  "message": "Senha alterada com sucesso!"
}
```

---

## 🧪 Testes de Validação

### 1. Testar Health Check
```bash
curl -X GET http://acme.localhost:8000/api/health/
```

### 2. Testar Registro
```bash
curl -X POST http://acme.localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 3. Testar Login
```bash
curl -X POST http://acme.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "TestPass123!"
  }'
```

### 4. Testar Profile (com token)
```bash
curl -X GET http://acme.localhost:8000/api/users/me/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 5. Testar Upload de Avatar
```bash
curl -X POST http://acme.localhost:8000/api/users/me/avatar/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "avatar=@path/to/image.jpg"
```

---

## 🔒 Segurança Implementada

### JWT Tokens
- ✅ Access token expira em 1 hora
- ✅ Refresh token expira em 7 dias
- ✅ Tokens rotacionados automaticamente
- ✅ Blacklist de tokens no logout

### Cookies
- ✅ HttpOnly (não acessível via JavaScript)
- ✅ Secure em produção (HTTPS only)
- ✅ SameSite=Lax (proteção CSRF)

### CORS
- ✅ Credentials permitidos
- ✅ Origins configuráveis via .env
- ✅ Regex para localhost com portas dinâmicas

### Validações
- ✅ Validação de senha com Django validators
- ✅ Email único
- ✅ Username único
- ✅ Confirmação de senha no registro
- ✅ Senha antiga no change password

### Upload de Arquivos
- ✅ Validação de tipo MIME
- ✅ Limite de tamanho (5MB)
- ✅ Nomes únicos com UUID
- ✅ Armazenamento seguro no MinIO

---

## 📊 Migrations Aplicadas

```
✅ accounts.0002_alter_user_options_user_avatar_user_bio_and_more
✅ token_blacklist.0001_initial
✅ token_blacklist.0002_outstandingtoken_jti_hex
✅ token_blacklist.0003_auto_20171017_2007
✅ token_blacklist.0004_auto_20171017_2013
✅ token_blacklist.0005_remove_outstandingtoken_jti
✅ token_blacklist.0006_auto_20171017_2113
✅ token_blacklist.0007_auto_20171017_2214
✅ token_blacklist.0008_migrate_to_bigautofield
✅ token_blacklist.0010_fix_migrate_to_bigautofield
✅ token_blacklist.0011_linearizes_history
✅ token_blacklist.0012_alter_outstandingtoken_user
```

**Aplicadas em:**
- ✅ Schema público (public)
- ✅ Todos os schemas de tenants

---

## 🎯 Integração Frontend

### Configuração Axios (React)

```typescript
// src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://acme.localhost:8000/api',
  withCredentials: true, // Importante para cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refresh = localStorage.getItem('refresh_token');
        const { data } = await axios.post(
          `${api.defaults.baseURL}/auth/token/refresh/`,
          { refresh }
        );
        
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

### Exemplos de Uso

```typescript
// Login
import api from '@/lib/api';

const login = async (email: string, password: string) => {
  const { data } = await api.post('/auth/login/', {
    username_or_email: email,
    password,
  });
  
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  
  return data.user;
};

// Get Profile
const getProfile = async () => {
  const { data } = await api.get('/users/me/');
  return data;
};

// Update Profile
const updateProfile = async (updates: Partial<User>) => {
  const { data } = await api.patch('/users/me/', updates);
  return data.user;
};

// Upload Avatar
const uploadAvatar = async (file: File) => {
  const formData = new FormData();
  formData.append('avatar', file);
  
  const { data } = await api.post('/users/me/avatar/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return data.avatar;
};
```

---

## 🐛 Troubleshooting

### Problema: CORS error ao fazer login
**Solução:** Verificar se `CORS_ALLOW_CREDENTIALS = True` está configurado

### Problema: Token não sendo aceito
**Solução:** Verificar se o header Authorization está no formato `Bearer <token>`

### Problema: Upload de avatar falha
**Solução:** 
1. Verificar se MinIO está rodando
2. Verificar credenciais no `.env`
3. Verificar se bucket existe

### Problema: Migrations não aplicam
**Solução:**
```bash
docker exec traksense-api python manage.py migrate_schemas --shared
docker exec traksense-api python manage.py migrate_schemas --tenant
```

---

## ✅ Checklist de Entrega

- [x] Dependências instaladas
- [x] Modelo User expandido
- [x] Serializers implementados
- [x] Views de autenticação criadas
- [x] URLs configuradas
- [x] JWT configurado com cookies
- [x] CORS configurado
- [x] MinIO storage configurado
- [x] Migrations aplicadas
- [x] Token blacklist funcionando
- [x] Upload de avatar operacional
- [x] Documentação completa

---

## 🎉 FASE 1 COMPLETA!

**Próxima fase:** FASE 2 - Catálogo de Ativos (Sites, Assets, Devices)

**Tempo estimado:** 1.5 semanas

**Arquivos modificados:**
- `requirements.txt` (2 dependências adicionadas)
- `apps/accounts/models.py` (User expandido)
- `apps/accounts/serializers.py` (6 serializers criados)
- `apps/accounts/views.py` (8 views implementadas)
- `apps/accounts/urls.py` (9 endpoints configurados)
- `apps/common/storage.py` (MinIO helpers criados)
- `config/settings/base.py` (JWT e CORS configurados)
- `config/urls.py` (accounts incluído)

**Total de linhas de código:** ~800 linhas
