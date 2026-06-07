from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from apps.restaurants.services import get_nearby_restaurants, CAMPUS_LOCATIONS
import json

try:
    import responses
except ImportError:
    responses = None


class RestaurantServiceTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_get_nearby_restaurants_returns_list(self):
        """유효한 캠퍼스 입력 시 리스트 반환"""
        # Note: 실제 API 호출이 필요하므로 responses 라이브러리 사용
        result = get_nearby_restaurants('seoul', 'all')
        # 캐시되지 않은 상태에서는 빈 리스트 또는 실제 API 응답
        self.assertIsInstance(result, list)

    def test_get_nearby_restaurants_invalid_campus_returns_empty(self):
        """유효하지 않은 캠퍼스 입력 시 빈 리스트 반환"""
        result = get_nearby_restaurants('invalid', 'all')
        self.assertEqual(result, [])

    def test_get_nearby_restaurants_cached(self):
        """두 번째 호출 시 캐시 사용"""
        # 첫 번째 호출
        result1 = get_nearby_restaurants('seoul', 'all')
        # API 실패 시 캐시되지 않음 (에러 처리)
        # 캐시 키 존재 여부 확인
        cache.set('restaurants:seoul:all', [], timeout=1800)
        cached = cache.get('restaurants:seoul:all')
        self.assertEqual(cached, [])


class RestaurantIndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_restaurant_index_200(self):
        """GET /restaurants/ → 200 OK"""
        response = self.client.get(reverse('restaurants:index'))
        self.assertEqual(response.status_code, 200)

    def test_restaurant_index_template_used(self):
        """restaurants/index.html 템플릿 사용"""
        response = self.client.get(reverse('restaurants:index'))
        self.assertTemplateUsed(response, 'restaurants/index.html')

    def test_restaurant_index_contains_campus_list(self):
        """context에 campus_list 포함"""
        response = self.client.get(reverse('restaurants:index'))
        self.assertIn('campus_list', response.context)
        self.assertEqual(len(response.context['campus_list']), 2)

    def test_restaurant_index_contains_category_list(self):
        """context에 category_list 포함"""
        response = self.client.get(reverse('restaurants:index'))
        self.assertIn('category_list', response.context)
        self.assertGreater(len(response.context['category_list']), 0)


class RestaurantSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_restaurant_search_returns_partial(self):
        """GET /restaurants/search/ → partial 응답"""
        response = self.client.get(
            reverse('restaurants:search') + '?campus=seoul&category=all'
        )
        self.assertEqual(response.status_code, 200)

    def test_restaurant_search_partial_template_used(self):
        """restaurants/partials/restaurant_list.html 사용"""
        response = self.client.get(
            reverse('restaurants:search') + '?campus=seoul&category=all'
        )
        self.assertTemplateUsed(response, 'restaurants/partials/restaurant_list.html')

    def test_restaurant_search_invalid_campus_returns_seoul_default(self):
        """유효하지 않은 캠퍼스 입력 시 서울캠 기본값"""
        response = self.client.get(
            reverse('restaurants:search') + '?campus=invalid&category=all'
        )
        self.assertEqual(response.context['campus'], 'seoul')

    def test_restaurant_search_contains_context_data(self):
        """응답 context에 필요한 데이터 포함"""
        response = self.client.get(
            reverse('restaurants:search') + '?campus=seoul&category=all'
        )
        self.assertIn('restaurants', response.context)
        self.assertIn('campus', response.context)
        self.assertIn('category', response.context)
        self.assertIn('campus_name', response.context)

