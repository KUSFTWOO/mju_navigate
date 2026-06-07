import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.navigation.services import get_transit_routes
import json

print("=== ODsay API Test ===\n")

# Test coordinates
# Seoul campus: 37.5803770223812, 126.921348530876
# Yongin campus: 37.2218072639192, 127.190183727516

result = get_transit_routes(37.5803770223812, 126.921348530876, 37.2218072639192, 127.190183727516)

if result:
    print("API Response Status: SUCCESS\n")

    # Check structure
    if 'result' in result:
        result_data = result['result']
        print(f"Result keys: {list(result_data.keys())}")

        if 'path' in result_data:
            paths = result_data['path']
            print(f"Number of paths: {len(paths)}")

            if paths:
                first = paths[0]
                print(f"\nFirst path info:")
                print(f"  totalTime: {first.get('totalTime')}")
                print(f"  pathType: {first.get('pathType')}")
                print(f"  fare: {first.get('fare')}")
                print(f"  subPath count: {len(first.get('subPath', []))}")
        else:
            print("No 'path' in result")
    else:
        print("No 'result' in response")
        print(f"Response keys: {list(result.keys())}")
else:
    print("API Response Status: FAILED (None)")
