#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.navigation.models import ShuttleRoute, ShuttleSchedule
from datetime import time

# Create missing route: 명지대역→용인캠
route, created = ShuttleRoute.objects.get_or_create(
    pk=6,
    defaults={
        'name': '명지대역 셔틀 (명지대역 → 용인캠)',
        'origin': 'mjustation',
        'destination': 'yongin_campus',
        'description': '명지대역 4번 출구 앞 승차',
        'is_active': True,
    }
)

if created:
    print("Created PK=6: mjustation → yongin_campus")
    # Add some schedules
    for day_type in ['weekday', 'saturday', 'sunday']:
        for hour, minute in [(7, 30), (8, 30), (9, 30), (14, 0), (16, 0), (18, 30)]:
            ShuttleSchedule.objects.create(
                route=route,
                departure_time=time(hour, minute),
                day_type=day_type,
                is_active=True,
            )
    print("Added schedules for PK=6")
else:
    print("PK=6 already exists")

# Check routes with yongin_campus as destination
routes = ShuttleRoute.objects.filter(destination='yongin_campus')
print("\nRoutes to yongin_campus:")
for r in routes:
    count = ShuttleSchedule.objects.filter(route=r).count()
    print(f"  PK={r.pk} {r.origin} → {r.destination} ({count} schedules)")
