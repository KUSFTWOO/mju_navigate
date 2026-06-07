from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse
import json
from .services import get_nearby_restaurants, get_coordinates_from_address, CAMPUS_LOCATIONS, CATEGORY_NAMES


class RestaurantView(TemplateView):
    template_name = 'restaurants/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 캠퍼스 목록 (좌표 정보 포함)
        campus_coords = {}
        for code, location in CAMPUS_LOCATIONS.items():
            coords = get_coordinates_from_address(location['address'])
            if coords:
                campus_coords[code] = coords
            else:
                # Geocoding 실패 시 기본값
                campus_coords[code] = {'lat': 0, 'lng': 0}

        campus_list = [
            {'code': 'seoul', 'name': '🏫 서울캠퍼스'},
            {'code': 'yongin', 'name': '🏭 용인캠퍼스'},
        ]

        # 카테고리 목록
        category_list = [
            {'code': 'all', 'name': '전체'},
            {'code': 'korean', 'name': '한식'},
            {'code': 'cafe', 'name': '카페'},
            {'code': 'chicken', 'name': '치킨'},
            {'code': 'chinese', 'name': '중식'},
            {'code': 'japanese', 'name': '일식'},
            {'code': 'western', 'name': '양식'},
            {'code': 'fastfood', 'name': '패스트푸드'},
        ]

        context.update({
            'campus_list': campus_list,
            'category_list': category_list,
            'default_campus': 'seoul',
            'campus_coords_json': json.dumps(campus_coords),
        })

        return context


class RestaurantSearchView(View):
    def get(self, request):
        campus = request.GET.get('campus', 'seoul')
        category = request.GET.get('category', 'all')
        radius = request.GET.get('radius', '1000')

        # 유효성 검사
        if campus not in CAMPUS_LOCATIONS:
            campus = 'seoul'

        # 반경 값 검증 (1000m, 3000m, 5000m만 허용)
        try:
            radius = int(radius)
            if radius not in [1000, 3000, 5000]:
                radius = 1000
        except (ValueError, TypeError):
            radius = 1000

        # 서비스 호출
        restaurants = get_nearby_restaurants(campus, category, radius)

        # HTMX partial 응답
        return render(
            request,
            'restaurants/partials/restaurant_list.html',
            {
                'restaurants': restaurants,
                'campus': campus,
                'category': category,
                'radius': radius,
                'campus_name': CAMPUS_LOCATIONS[campus]['name'],
            }
        )
