# TrakSense Backend - Multi-Tenant IoT/HVAC Monitoring Platform

> **AI Coding Assistant Instructions** - Guia completo para desenvolvimento do backend Django multi-tenant

---

## ⚠️ CRITICAL: File Organization Rules

### 🚨 NEVER CREATE FILES IN THE ROOT DIRECTORY

**ALWAYS follow these rules when creating new files:**

#### 📚 Documentation Files (.md)
❌ **NEVER** create in root: `c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\`
✅ **ALWAYS** create in: `c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\docs\`

**Specific locations:**
- **Fase docs** → `docs/fases/FASE_*.md`
- **Implementation docs** → `docs/implementacao/IMPLEMENTACAO_*.md`
- **Guides** → `docs/guias/GUIA_*.md`
- **EMQX docs** → `docs/emqx/EMQX_*.md`
- **Validations** → `docs/validacoes/VALIDACAO_*.md` or `RELATORIO_*.md`
- **Bugfixes** → `docs/bugfixes/BUGFIX_*.md` or `CORRECAO_*.md`
- **General docs** → `docs/` (checklists, commands, etc)

#### 🔧 Python Scripts (.py)
❌ **NEVER** create in root: `c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\`
✅ **ALWAYS** create in: `c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\scripts\`

**Specific locations:**
- **Test scripts** → `scripts/tests/test_*.py`
- **Setup/Create scripts** → `scripts/setup/create_*.py`
- **Verification scripts** → `scripts/verification/check_*.py`
- **Maintenance scripts** → `scripts/maintenance/fix_*.py` or `cleanup_*.py`
- **Utility scripts** → `scripts/utils/` (provision, publish, sync, debug, set, delete)

#### 📋 Naming Conventions
| Prefix | Location | Example |
|--------|----------|---------|
| `FASE_` | `docs/fases/` | `docs/fases/FASE_7_ANALYTICS.md` |
| `IMPLEMENTACAO_` | `docs/implementacao/` | `docs/implementacao/IMPLEMENTACAO_ANALYTICS.md` |
| `GUIA_` | `docs/guias/` | `docs/guias/GUIA_TESTE_ANALYTICS.md` |
| `EMQX_` | `docs/emqx/` | `docs/emqx/EMQX_SECURITY.md` |
| `VALIDACAO_` | `docs/validacoes/` | `docs/validacoes/VALIDACAO_ANALYTICS.md` |
| `BUGFIX_` | `docs/bugfixes/` | `docs/bugfixes/BUGFIX_ANALYTICS_ERROR.md` |
| `test_` | `scripts/tests/` | `scripts/tests/test_analytics.py` |
| `create_` | `scripts/setup/` | `scripts/setup/create_analytics_data.py` |
| `check_` | `scripts/verification/` | `scripts/verification/check_analytics.py` |
| `fix_` | `scripts/maintenance/` | `scripts/maintenance/fix_analytics.py` |
| `cleanup_` | `scripts/maintenance/` | `scripts/maintenance/cleanup_analytics.py` |

#### ✅ Exceptions (Files allowed in root)
ONLY these files belong in the root:
- `README.md` (main project readme)
- `INDEX.md` (navigation index)
- `NAVEGACAO.md` (quick navigation guide)
- `REORGANIZACAO.md` (reorganization documentation)
- `manage.py` (Django management)
- `gunicorn.conf.py` (server config)
- `Makefile` (build commands)
- `requirements.txt` (Python dependencies)
- `.env`, `.env.example` (environment config)
- `.gitignore` (git config)
- `celerybeat-schedule` (Celery temp file)

#### 🔍 Before Creating Any File
1. **Check the naming** - Does it follow conventions?
2. **Determine the type** - Documentation or Script?
3. **Find the correct folder** - Use the table above
4. **Create in the right place** - Never in root!

#### 📖 Reference Files
- **AI Instructions**: `.github/ai-instructions/` - **⭐ READ THIS FIRST!**
- **Full index**: `INDEX.md` - Complete project navigation
- **Docs index**: `docs/README.md` - Documentation organization
- **Scripts index**: `scripts/README.md` - Scripts organization
- **Reorganization**: `REORGANIZACAO.md` - Why and how we organized

---

## 🏗️ Architecture Overview

**Product:** B2B multi-tenant SaaS for HVAC/IoT monitoring, telemetry, alerts, and analytics.

**Tech Stack:**
- **Framework:** Django 5 + Django REST Framework
- **Multi-Tenancy:** django-tenants (PostgreSQL schema-per-tenant)
- **Database:** PostgreSQL 16 + TimescaleDB extension
- **MQTT Broker:** EMQX for IoT device ingestion
- **Cache/Queue:** Redis (Celery broker, cache, rate limiting)
- **Object Storage:** MinIO (S3-compatible) for avatars, reports
- **Async Tasks:** Celery + Celery Beat
- **Auth:** JWT in HttpOnly cookies (access + refresh tokens)
- **API Docs:** OpenAPI 3 (drf-spectacular)

**Deployment:**
- **Development:** Docker Compose with 10+ services
- **Production:** Kubernetes-ready architecture

---

## 🔒 SECURITY: Recent Fixes (Nov 2025)

**⚠️ CRITICAL UPDATES - All security vulnerabilities have been addressed:**

### Backend Security Fixes (8/8 Implemented)

1. **✅ Registration Exploit (CRÍTICO)**
   - **File:** `apps/accounts/views.py` (lines 48-115)
   - **Fix:** Restricted registration to public schema only, requires `invitation_token` for tenant domains
   - **Impact:** Prevents self-admin on any tenant domain

2. **✅ MQTT Authentication (CRÍTICO)**
   - **File:** `apps/ingest/views.py` (lines 42-90)
   - **Fix:** Requires `x-device-token` header with HMAC SHA256 signature
   - **Config:** `INGESTION_SECRET` environment variable (REQUIRED in production)
   - **Impact:** Blocks unauthenticated data injection

3. **✅ Sensor Lookup FieldError (CRÍTICO)**
   - **File:** `apps/alerts/tasks.py` (line 180)
   - **Fix:** Changed `sensor_id` to `tag` field
   - **Impact:** All multi-parameter alerts now work (was 0% functional)

4. **✅ Duplicate Handling Race Condition**
   - **File:** `apps/ingest/views.py` (line 382)
   - **Fix:** Added `ignore_conflicts=True` to `bulk_create()`
   - **Impact:** Prevents batch drops on concurrent ingestions

5. **✅ Auto-Site Assignment Corruption**
   - **File:** `apps/ingest/views.py` (lines 530-548)
   - **Fix:** Rejects missing site metadata instead of using `.first()`
   - **Impact:** Preserves asset hierarchy integrity

6. **✅ N+1 Queries (Performance)**
   - **File:** `apps/alerts/tasks.py` (lines 40-60)
   - **Fix:** Added `prefetch_related()` for parameters/devices/sensors
   - **Impact:** Rule evaluation time reduced by ~97%

7. **✅ Duplicate Test Files**
   - **Action:** Deleted `test_bug_fixes_simple.py`, kept `test_bug_fixes.py`
   - **Impact:** Single source of truth for regression tests

8. **✅ UTF-8 Encoding**
   - **File:** `.editorconfig` (created)
   - **Fix:** Enforces UTF-8 charset for all new files
   - **Impact:** Prevents mojibake in future files

### Required Environment Variables

```bash
# config/settings/base.py
INGESTION_SECRET=<64_hex_chars>  # Generate with: secrets.token_hex(32)
DJANGO_SECRET_KEY=<100_hex_chars>  # Generate with: secrets.token_hex(50)
DEBUG=False  # MUST be False in production
ALLOWED_HOSTS=umc.production.com,acme.production.com
```

### Security Validation Checklist

**Before deploying:**
- [ ] `INGESTION_SECRET` configured
- [ ] Registration blocked on tenant domains (returns 403)
- [ ] MQTT endpoint requires valid device token (returns 401)
- [ ] Alerts firing correctly (no FieldError)
- [ ] Concurrent ingestions don't drop batches
- [ ] Sites not auto-assigned arbitrarily

**Documentation:** See `CORRECOES_SEGURANCA_COMPLETAS.md` for full details

---

## � RECENT FIXES: Architecture & Performance (Nov 2025)

**⚠️ CRITICAL UPDATES - Additional fixes beyond security audit:**

### Backend Fixes (8 additional corrections)

1. **✅ Device Heartbeat Handler**
   - File: `apps/assets/views.py:472`
   - Fix: Pass `new_status='ONLINE'` and optional `timestamp` to `device.update_status()`
   - Impact: Fixes TypeError on all POST /api/devices/{id}/heartbeat/ requests

2. **✅ Legacy Rules Sensor Lookup**
   - File: `apps/alerts/tasks.py:301`
   - Fix: Changed `Sensor.objects.filter(sensor_id=...)` to `filter(tag=...)`
   - Impact: Legacy alert rules now trigger correctly (sensor_id field doesn't exist)

3. **✅ INGESTION_SECRET Enforcement**
   - File: `apps/ingest/views.py:69-96`
   - Fix: Return 401 if INGESTION_SECRET not configured (was just logging warning)
   - Impact: Prevents unauthorized telemetry ingestion in production

4. **✅ SMS/WhatsApp Mock Status**
   - File: `apps/alerts/services/notification_service.py:232-309`
   - Fix: Return `'skipped': True` instead of `'sent': True` for mock implementations
   - Impact: Accurate compliance reporting until real providers integrated

5. **✅ Redundant exists() Checks**
   - File: `apps/ingest/views.py:359-386`
   - Fix: Removed `.exists()` checks before `bulk_create(..., ignore_conflicts=True)`
   - Impact: Reduces N database roundtrips per ingestion batch

6. **✅ N+1 Query Optimization**
   - Files: `apps/assets/views.py` + `apps/assets/serializers.py`
   - Fix: Added `annotate()` in viewsets for asset_count, device_count, sensor_count
   - Impact: Serializers use pre-computed annotations instead of per-object queries

7. **✅ Asset History Pagination**
   - File: `apps/ingest/api_views_extended.py:660-703`
   - Fix: Added MAX_RAW_RESULTS (10k) and MAX_AGG_RESULTS (2k) limits
   - Impact: Prevents memory exhaustion with large time ranges

8. **✅ Force Unique Secrets**
   - File: `config/settings/base.py:19, 324-327`
   - Fix: Validate SECRET_KEY and MINIO credentials at startup
   - Impact: Production deployments must use unique secrets (no defaults)

### Required Actions After Deployment

**Environment Variables:**
```bash
DJANGO_SECRET_KEY=<100_hex_chars>  # Generate with: secrets.token_hex(50)
INGESTION_SECRET=<64_hex_chars>    # Generate with: secrets.token_hex(32)
MINIO_ACCESS_KEY=<unique_value>    # Do not use 'minioadmin'
MINIO_SECRET_KEY=<unique_value>    # Do not use 'minioadmin123'
DEBUG=False
```

**Validation Checklist:**
- [ ] All device heartbeats succeed (no TypeError)
- [ ] Legacy alert rules evaluate correctly
- [ ] Telemetry ingestion requires valid INGESTION_SECRET
- [ ] SMS/WhatsApp notifications show as "skipped" in logs
- [ ] Asset list API loads in <500ms for 1000+ assets
- [ ] History API truncates with warning for large ranges
- [ ] Production secrets validated at startup

---

## �📦 Project Structure

```
traksense-backend/
├── apps/
│   ├── accounts/          # User authentication, JWT, profiles
│   ├── assets/            # Sites, Assets, Devices, Sensors (CRUD)
│   ├── tenants/           # Tenant and Domain models
│   ├── ingest/            # MQTT telemetry ingestion, TimescaleDB queries
│   ├── ops/               # Operations panel (public schema only)
│   └── common/            # Shared utilities, health check
│
├── config/
│   ├── settings/          # Django settings (base, dev, prod)
│   ├── urls.py            # Root URL configuration
│   ├── celery.py          # Celery app configuration
│   └── wsgi.py / asgi.py  # WSGI/ASGI entry points
│
├── docker/
│   ├── Dockerfile         # Multi-stage production image
│   ├── docker-compose.yml # Development stack
│   └── nginx.conf         # Nginx reverse proxy config
│
├── migrations/            # Custom multi-tenant migrations
├── tests/                 # pytest test suite
├── manage.py              # Django management script
├── Makefile               # Development commands
└── requirements/
    ├── base.txt           # Core dependencies
    ├── dev.txt            # Development tools
    └── prod.txt           # Production dependencies
```

---

## 🎯 Multi-Tenant Architecture

### Schema-Per-Tenant Isolation

**django-tenants** provides complete data isolation using PostgreSQL schemas:

**Public Schema:**
- `tenants_tenant` - Tenant registry
- `tenants_domain` - Domain-to-tenant mapping
- `accounts_user` - Global user table
- `accounts_membership` - User-tenant relationships

**Tenant Schemas (e.g., "uberlandia_medical_center"):**
- `assets_site`, `assets_asset`, `assets_device`, `assets_sensor`
- `ingest_telemetryreading` (TimescaleDB hypertable)
- `ingest_devicestatus`, `ingest_sensorstatus`
- All business data isolated per tenant

### Domain Routing

**Configuration:** `TENANT_MODEL_DOMAIN_FIELD = 'domain'`

**Example mappings:**
- `umc.localhost` → UMC tenant (schema: uberlandia_medical_center)
- `api` → Public schema (for ops panel, tenant admin)
- `acme.localhost` → ACME tenant (schema: acme_corp)

**Middleware:** `tenant_schemas.middleware.TenantMiddleware`
- Resolves tenant from hostname
- Sets `connection.schema_name` for all queries
- Isolates data automatically

---

## 🎯 CRITICAL: MQTT Topic-Based Validation

### ⚠️ ALWAYS Use MQTT Topic as Source of Truth for Sensors

**RULE:** When dealing with sensors, devices, or telemetry relationships, **ALWAYS validate and organize data based on MQTT topic structure**, not by individual device IDs.

#### MQTT Topic Structure
```
tenants/{tenant_slug}/sites/{site_name}/assets/{asset_tag}/telemetry
```

**Example:**
```
tenants/umc/sites/Uberlândia Medical Center/assets/CHILLER-001/telemetry
```

#### Why This Matters

❌ **WRONG APPROACH (Device-centric):**
```python
# Searching by device_id only shows sensors from ONE device
sensors = Sensor.objects.filter(device__mqtt_client_id=device_id)

# Problem: If an Asset has multiple devices (e.g., old device + new gateway),
# you'll only see sensors from ONE device at a time
```

✅ **CORRECT APPROACH (Topic/Asset-centric):**
```python
# Searching by Asset shows sensors from ALL devices of that asset
sensors = Sensor.objects.filter(device__asset=asset)

# This automatically includes sensors from all devices linked to the asset,
# respecting the MQTT topic hierarchy: tenant → site → asset
```

#### Implementation Guidelines

**Backend (Django):**
1. **Ingest endpoint** (`apps/ingest/views.py`):
   - Parse topic to extract: `tenant`, `site`, `asset_tag`
   - Auto-create hierarchy: Tenant → Site → Asset → Device → Sensors
   - Link sensors to Asset via Device relationship

2. **API endpoints** should return sensors by Asset, not by Device:
   ```python
   # ✅ CORRECT
   GET /api/assets/{asset_id}/sensors/
   
   # ❌ AVOID (unless specifically needed)
   GET /api/devices/{device_id}/sensors/
   ```

**Frontend (React/TypeScript):**
1. **Load sensors by Site or Asset**:
   ```typescript
   // ✅ CORRECT: Get all sensors from all assets in site
   assetsService.getBySite(siteId)
     .then(assets => {
       return Promise.all(
         assets.map(asset => assetsService.getSensors(asset.id))
       );
     });
   
   // ❌ AVOID: Load by device (shows only partial data)
   devicesService.listBySite(siteId)
     .then(devices => {
       loadTelemetry(devices[0].mqtt_client_id); // Only ONE device!
     });
   ```

2. **SensorsPage pattern**:
   ```typescript
   // Load ALL sensors from ALL assets of selected site
   // This respects MQTT topic hierarchy
   useEffect(() => {
     if (!currentSite?.id) return;
     
     assetsService.getBySite(currentSite.id)
       .then(response => {
         const assets = response.results;
         // For each asset, get its sensors (from ALL devices)
         const sensorsPromises = assets.map(asset => 
           assetsService.getSensors(asset.id)
         );
         return Promise.all(sensorsPromises);
       });
   }, [currentSite?.id]);
   ```

#### Auto-Creation Flow (MQTT → Database)

```
1. MQTT message arrives on topic:
   tenants/umc/sites/UMC Hospital/assets/CHILLER-001/telemetry

2. Ingest parser extracts:
   - tenant: "umc"
   - site: "UMC Hospital"
   - asset: "CHILLER-001"
   - device_id: (from payload or client_id)

3. Auto-create if not exists:
   ├─ Tenant (umc) ✅
   ├─ Site (UMC Hospital) ✅
   ├─ Asset (CHILLER-001) ✅
   ├─ Device (gateway MAC address) ✅
   └─ Sensors (temperature, humidity, etc.) ✅

4. All sensors linked to Asset via Device
   - Sensor.device → Device
   - Device.asset → Asset
   - Asset.site → Site
```

#### Benefits of Topic-Based Validation

✅ **Automatic multi-device support:** Asset can have multiple gateways/controllers
✅ **Hierarchical consistency:** Data organization mirrors physical infrastructure
✅ **Scalability:** Add new devices without code changes
✅ **Multi-tenant isolation:** Topic includes tenant slug
✅ **Frontend simplicity:** Load by Site/Asset, not by individual devices

#### Common Mistakes to Avoid

❌ Loading sensors by `device_id` when you need ALL sensors of an asset
❌ Hardcoding device selection (e.g., `devices[0]`)
❌ Ignoring Asset hierarchy in favor of flat Device lists
❌ Not using topic structure for auto-creation
❌ Frontend showing partial data because it loads only one device

#### Reference Implementation

See:
- **Backend:** `apps/ingest/views.py` (IngestView)
- **Backend:** `apps/ingest/parsers/khomp_senml.py` (KhompSenMLParser)
- **Frontend:** `src/components/pages/SensorsPage.tsx` (topic-based loading)
- **Frontend:** `src/components/pages/AssetDetailsPage.tsx` (AssetTelemetry tab)

### URL Configuration

**Public Schema:**
```python
# config/urls_public.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('ops/', include('apps.ops.urls')),  # Operations panel
    path('health/', health_check),
]
```

**Tenant Schemas:**
```python
# config/urls.py (ROOT_URLCONF)
urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('assets/', include('apps.assets.urls')),
    path('ingest/', include('apps.ingest.urls')),
    # ... other tenant-scoped routes
]
```

---

## 🗄️ Database Schema

### Core Models

#### **Tenant** (`tenants.Tenant`)
```python
class Tenant(TenantMixin):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    auto_create_schema = True
    auto_drop_schema = True  # Be careful in production!
```

#### **Domain** (`tenants.Domain`)
```python
class Domain(DomainMixin):
    tenant = models.ForeignKey(Tenant)
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=True)
```

#### **User** (`accounts.User`)
```python
class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/')
    is_active = models.BooleanField(default=True)
    # ... JWT-compatible auth fields
```

#### **Asset Hierarchy** (`assets` app)
```python
Site (location/building)
  └── Asset (HVAC equipment)
       └── Device (IoT hardware)
            └── Sensor (measurement points)

# Example: UMC Hospital → Chiller-001 → ESP32-01 → Temp Sensor
```

#### **Telemetry** (`ingest.TelemetryReading`)
```python
class TelemetryReading(models.Model):
    sensor = models.ForeignKey(Sensor)
    timestamp = models.DateTimeField()
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        # TimescaleDB hypertable (partitioned by timestamp)
        db_table = 'telemetry_readings'
```

### TimescaleDB Configuration

**Hypertable Creation:**
```sql
SELECT create_hypertable('telemetry_readings', 'timestamp');

-- Continuous aggregate for hourly averages
CREATE MATERIALIZED VIEW telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    sensor_id,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as count
FROM telemetry_readings
GROUP BY hour, sensor_id;
```

---

## 📡 API Endpoints

### Authentication (`accounts` app)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register/` | Create new tenant + admin user |
| POST | `/auth/login/` | Login (sets HttpOnly cookies) |
| POST | `/auth/logout/` | Logout (clears cookies) |
| POST | `/auth/refresh/` | Refresh access token |
| GET | `/auth/me/` | Current user info |
| PATCH | `/auth/me/` | Update user profile |
| POST | `/auth/change-password/` | Change password |
| POST | `/auth/avatar/` | Upload avatar (S3) |

### Assets (`assets` app)

**ViewSets (Standard DRF CRUD):**
- `SiteViewSet` → `/assets/sites/`
- `AssetViewSet` → `/assets/assets/`
- `DeviceViewSet` → `/assets/devices/`
- `SensorViewSet` → `/assets/sensors/`

**Common Patterns:**
```http
GET    /assets/sites/                    # List (filtered, paginated)
POST   /assets/sites/                    # Create
GET    /assets/sites/{id}/               # Retrieve
PUT    /assets/sites/{id}/               # Full update
PATCH  /assets/sites/{id}/               # Partial update
DELETE /assets/sites/{id}/               # Delete

# Query Parameters:
?status=online|offline|warning
?site={site_id}
?search={query}
?page={page_number}
```

### Telemetry (`ingest` app)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/` | MQTT webhook ingestion |
| GET | `/ingest/telemetry/` | Query telemetry (time-range, aggregates) |
| GET | `/ingest/latest/{device_id}/` | Latest readings per sensor |
| GET | `/ingest/history/{device_id}/` | Historical data (time-series) |
| GET | `/ingest/summary/{device_id}/` | Summary statistics |
| GET | `/ingest/aggregates/` | Time-series aggregates (hourly, daily) |
| GET | `/ingest/readings/` | Raw readings (filtered) |

**Example Telemetry Query:**
```http
GET /ingest/history/ESP32-01/?from=2025-01-01T00:00:00Z&to=2025-01-02T00:00:00Z&interval=5m&sensor_type=temperature

Response:
{
  "device_id": "ESP32-01",
  "data": [
    {
      "timestamp": "2025-01-01T00:00:00Z",
      "sensor_type": "temperature",
      "value": 23.5,
      "unit": "°C"
    },
    ...
  ]
}
```

---

## 🔐 Authentication & Authorization

### JWT in HttpOnly Cookies

**Pattern:**
1. Client sends credentials to `/auth/login/`
2. Server validates and issues JWT tokens
3. Tokens set as HttpOnly cookies (not accessible via JavaScript)
4. Client includes cookies in all subsequent requests
5. Server validates access token on each request
6. Refresh token used to renew access token

**Token Lifetimes:**
- Access token: 15 minutes
- Refresh token: 7 days

**Implementation:**
```python
# apps/accounts/views.py
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(**serializer.validated_data)
        if not user:
            raise AuthenticationFailed("Invalid credentials")
        
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        
        response = Response({"message": "Login successful"})
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite='Lax'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return response
```

### Permission Classes

**Built-in:**
- `IsAuthenticated` - Requires valid JWT
- `IsAdminUser` - Requires staff status

**Custom:**
```python
class IsTenantMember(BasePermission):
    def has_permission(self, request, view):
        # User must belong to current tenant schema
        tenant = connection.tenant
        return Membership.objects.filter(
            tenant=tenant,
            user=request.user,
            is_active=True
        ).exists()
```

---

## 🔄 MQTT Integration (EMQX)

### Topic Structure

```
tenants/{tenant_slug}/devices/{device_id}/sensors/{sensor_id}
```

**Example:**
```
tenants/umc/devices/ESP32-01/sensors/temp_001
```

### EMQX Rule Engine

**Webhook to Django:**
```sql
SELECT
  payload.value as value,
  payload.unit as unit,
  payload.timestamp as timestamp,
  topic
FROM "tenants/+/devices/+/sensors/+"
```

**Action:** HTTP POST to `http://api:8000/ingest/`

**Payload:**
```json
{
  "device_id": "ESP32-01",
  "sensor_id": "temp_001",
  "tenant": "umc",
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Ingestion View

```python
# apps/ingest/views.py
class IngestView(APIView):
    permission_classes = [AllowAny]  # EMQX uses API key in payload
    
    def post(self, request):
        # Validate API key, tenant, device
        # Create TelemetryReading in correct tenant schema
        # Handle validation (unit, range, sensor exists)
        # Return 201 or 400
        pass
```

---

## ⚙️ Celery Tasks

### Configuration

**Broker:** Redis (`redis://redis:6379/0`)

**Queues:**
- `celery` - Default queue
- `telemetry` - High-volume ingestion tasks
- `reports` - Long-running report generation

### Example Tasks

```python
# apps/ingest/tasks.py
@shared_task
def aggregate_telemetry_hourly(tenant_schema):
    with schema_context(tenant_schema):
        # Refresh TimescaleDB continuous aggregate
        # Calculate hourly averages, min, max
        # Update DeviceStatus last_seen
        pass

@shared_task
def check_sensor_thresholds(tenant_schema, sensor_id):
    with schema_context(tenant_schema):
        # Query latest reading
        # Compare against thresholds
        # Create alert if breached
        pass
```

### Celery Beat Schedule

```python
# config/celery.py
app.conf.beat_schedule = {
    'aggregate-telemetry-hourly': {
        'task': 'apps.ingest.tasks.aggregate_telemetry_hourly',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

---

## 🧪 Testing

### pytest Configuration

**File:** `pytest.ini`
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=apps --cov-report=html --cov-report=term-missing
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures (API client, tenants, users)
├── test_auth.py             # Authentication flow
├── test_assets.py           # Asset CRUD operations
├── test_telemetry.py        # Ingestion and queries
└── test_multi_tenant.py     # Schema isolation
```

### Example Test

```python
import pytest
from django.test import override_settings
from tenant_schemas.utils import schema_context

@pytest.mark.django_db
def test_asset_creation_isolated_by_tenant(tenant_umc, tenant_acme, api_client):
    # Create asset in UMC schema
    with schema_context('uberlandia_medical_center'):
        api_client.force_authenticate(user=tenant_umc_user)
        response = api_client.post('/assets/assets/', {
            'name': 'Chiller-001',
            'type': 'chiller',
            'site': site_umc.id
        })
        assert response.status_code == 201
        asset_id = response.data['id']
    
    # Verify asset NOT visible in ACME schema
    with schema_context('acme_corp'):
        api_client.force_authenticate(user=tenant_acme_user)
        response = api_client.get(f'/assets/assets/{asset_id}/')
        assert response.status_code == 404
```

---

## 🛠️ Development Commands

### Makefile

```makefile
.PHONY: dev migrate seed test lint format

dev:
	docker-compose up -d

migrate:
	python manage.py migrate_schemas --noinput

seed:
	python manage.py seed_dev  # Creates UMC tenant, sample data

test:
	pytest tests/ -v

lint:
	ruff check apps/
	mypy apps/

format:
	black apps/
	isort apps/

ci: lint test
```

### Docker Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Enter Django shell
docker-compose exec api python manage.py shell

# Create superuser (public schema)
docker-compose exec api python manage.py createsuperuser

# Migrate all tenant schemas
docker-compose exec api python manage.py migrate_schemas
```

### Service URLs (Development)

- **Django API:** http://localhost:8000/api
- **Nginx (proxy):** http://localhost
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379
- **EMQX Dashboard:** http://localhost:18083 (admin/public)
- **MinIO Console:** http://localhost:9001 (dev/devsecret)
- **Mailpit (email):** http://localhost:8025

---

## 🔒 Security Best Practices

### 1. Never Use `eval()` for Formulas
```python
# Bad ✗
result = eval(formula_string)

# Good ✓
from formulaparser import safe_evaluate
result = safe_evaluate(formula_string, whitelist=['avg', 'sum', 'min', 'max'])
```

### 2. Validate Telemetry Payloads
```python
# Check sensor exists, unit matches, value in range
sensor = Sensor.objects.get(id=payload['sensor_id'])
if payload['unit'] != sensor.unit:
    raise ValidationError("Unit mismatch")
if not (sensor.min_value <= payload['value'] <= sensor.max_value):
    raise ValidationError("Value out of range")
```

### 3. Rate Limiting
```python
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class IngestView(APIView):
    throttle_classes = [UserRateThrottle]  # 1000/hour per device
```

### 4. S3 Signed URLs
```python
from django.core.files.storage import default_storage

# Generate signed URL with expiration
url = default_storage.url(file_path, expire=3600)  # 1 hour
```

### 5. SQL Injection Prevention
```python
# Django ORM is safe by default
Asset.objects.filter(name=user_input)  # Parameterized ✓

# Raw SQL - use parameters
cursor.execute("SELECT * FROM assets WHERE name = %s", [user_input])  # ✓
```

---

## 📝 Code Style & Conventions

### Python Style

**Formatter:** Black (line length: 100)
**Import Order:** isort (5 sections)
**Linter:** Ruff (replaces flake8, pylint)

### Model Conventions

```python
class Asset(models.Model):
    """HVAC equipment (Chiller, AHU, VRF, etc.)"""
    
    # Foreign keys first
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='assets')
    
    # Required fields
    name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=50, choices=AssetType.choices)
    
    # Optional fields
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['site', 'asset_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.asset_type})"
```

### ViewSet Conventions

```python
class AssetViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for HVAC assets.
    
    Filters: status, site, search
    Permissions: Tenant member only
    """
    queryset = Asset.objects.select_related('site').prefetch_related('devices')
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'site', 'asset_type']
    search_fields = ['name', 'model', 'serial_number']
    ordering_fields = ['name', 'created_at']
```

---

## 📚 Migration Patterns

### Tenant-Aware Migrations

```python
# migrations/0002_create_asset.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('name', models.CharField(max_length=255)),
                # ...
            ],
        ),
    ]
```

**Run migrations:**
```bash
# Migrate public schema
python manage.py migrate_schemas --schema=public

# Migrate all tenant schemas
python manage.py migrate_schemas --noinput

# Migrate specific tenant
python manage.py migrate_schemas --schema=uberlandia_medical_center
```

---

## 🚀 Deployment Checklist

### Environment Variables (Production)

```bash
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=api.traksense.com,*.traksense.com
CORS_ALLOWED_ORIGINS=https://app.traksense.com

DB_URL=postgres://user:pass@db.example.com:5432/traksense
REDIS_URL=redis://redis.example.com:6379/0

AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
AWS_STORAGE_BUCKET_NAME=traksense-files
AWS_S3_REGION_NAME=us-east-1

SENTRY_DSN=https://...@sentry.io/...
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>

EMQX_MQTT_URL=mqtt://emqx.example.com:1883
EMQX_WEBHOOK_SECRET=<random-secret>
```

### Security Headers

```python
# config/settings/prod.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 🎯 File Creation Examples (AI Reference)

### Example 1: Creating Phase Documentation
```
❌ WRONG: create_file("FASE_7_ANALYTICS.md", ...)
✅ CORRECT: create_file("docs/fases/FASE_7_ANALYTICS.md", ...)
```

### Example 2: Creating Implementation Doc
```
❌ WRONG: create_file("IMPLEMENTACAO_DASHBOARD.md", ...)
✅ CORRECT: create_file("docs/implementacao/IMPLEMENTACAO_DASHBOARD.md", ...)
```

### Example 3: Creating Test Script
```
❌ WRONG: create_file("test_analytics.py", ...)
✅ CORRECT: create_file("scripts/tests/test_analytics.py", ...)
```

### Example 4: Creating Setup Script
```
❌ WRONG: create_file("create_analytics_data.py", ...)
✅ CORRECT: create_file("scripts/setup/create_analytics_data.py", ...)
```

### Example 5: Creating Guide
```
❌ WRONG: create_file("GUIA_ANALYTICS.md", ...)
✅ CORRECT: create_file("docs/guias/GUIA_ANALYTICS.md", ...)
```

### Example 6: Creating Bugfix Doc
```
❌ WRONG: create_file("BUGFIX_DASHBOARD_ERROR.md", ...)
✅ CORRECT: create_file("docs/bugfixes/BUGFIX_DASHBOARD_ERROR.md", ...)
```

### Decision Tree for File Placement

```
Is it a .md file?
├─ Yes → Is it documentation?
│  ├─ Yes → Check prefix:
│  │  ├─ FASE_* → docs/fases/
│  │  ├─ IMPLEMENTACAO_* → docs/implementacao/
│  │  ├─ GUIA_* → docs/guias/
│  │  ├─ EMQX_* → docs/emqx/
│  │  ├─ VALIDACAO_* or RELATORIO_* → docs/validacoes/
│  │  ├─ BUGFIX_* or CORRECAO_* → docs/bugfixes/
│  │  └─ Other → docs/
│  └─ No → Is it README.md or INDEX.md?
│     ├─ Yes → Root is OK
│     └─ No → Ask for clarification
│
└─ No → Is it a .py file?
   ├─ Yes → Check prefix:
   │  ├─ test_* → scripts/tests/
   │  ├─ create_* → scripts/setup/
   │  ├─ check_* → scripts/verification/
   │  ├─ fix_* or cleanup_* → scripts/maintenance/
   │  ├─ provision_*, publish_*, sync_*, debug_*, set_*, delete_*, verify_* → scripts/utils/
   │  └─ No prefix → Ask for purpose, then place appropriately
   │
   └─ No → Is it config file (manage.py, Makefile, requirements.txt, .env)?
      ├─ Yes → Root is OK
      └─ No → Ask for clarification
```

---

## 📖 Additional Resources

- **Django Tenants Docs:** https://django-tenants.readthedocs.io
- **TimescaleDB Docs:** https://docs.timescale.com
- **EMQX Docs:** https://www.emqx.io/docs
- **DRF Spectacular:** https://drf-spectacular.readthedocs.io
- **Celery Docs:** https://docs.celeryq.dev

**Project Organization:**
- **Navigation Index:** `INDEX.md` - Complete project guide
- **Documentation Index:** `docs/README.md` - All documentation organized
- **Scripts Index:** `scripts/README.md` - All scripts organized
- **Reorganization Doc:** `REORGANIZACAO.md` - Why files are organized this way

---

**Last Updated:** 30 de outubro de 2025
**Django Version:** 5.0
**Python Version:** 3.11+
**File Organization:** Strictly enforced - see top of document
