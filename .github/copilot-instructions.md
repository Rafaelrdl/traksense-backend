# TrakSense Backend - Multi-Tenant IoT/HVAC Monitoring Platform

> **AI Coding Assistant Instructions** - Guia completo para desenvolvimento do backend Django multi-tenant

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

## 📦 Project Structure

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

## 📖 Additional Resources

- **Django Tenants Docs:** https://django-tenants.readthedocs.io
- **TimescaleDB Docs:** https://docs.timescale.com
- **EMQX Docs:** https://www.emqx.io/docs
- **DRF Spectacular:** https://drf-spectacular.readthedocs.io
- **Celery Docs:** https://docs.celeryq.dev

---

**Last Updated:** 2025
**Django Version:** 5.0
**Python Version:** 3.11+
