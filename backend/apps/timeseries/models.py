"""
Timeseries models.

Note: ts_measure table is created via SQL migration (not Django ORM)
because it uses TimescaleDB-specific features (hypertable, continuous aggregates, etc.)
"""
from django.db import models

# No Django models here - ts_measure is created via RunSQL in migrations
# This allows us to use TimescaleDB features directly
