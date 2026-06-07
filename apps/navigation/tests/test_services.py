from django.test import TestCase
from django.core.cache import cache
import responses
from apps.navigation.services import get_transit_routes


class TransitRoutesServiceTestCase(TestCase):
    def setUp(self):
        cache.clear()

    @responses.activate
    def test_get_transit_routes_success(self):
        """ODsay API 호출 성공"""
        responses.add(
            responses.GET,
            'https://api.odsay.com/v1/api/searchPubTransPathT',
            json={
                'result': {
                    'path': [
                        {
                            'totalTime': 45,
                            'pathType': '1',
                            'fare': 1250,
                        }
                    ]
                }
            },
            status=200
        )

        result = get_transit_routes(37.5712, 126.9258, 37.3391, 127.0955)

        self.assertIsNotNone(result)
        self.assertIn('result', result)

    def test_get_transit_routes_api_error_returns_none(self):
        """API 오류 시 None 반환"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                'https://api.odsay.com/v1/api/searchPubTransPathT',
                status=500
            )

            result = get_transit_routes(37.5712, 126.9258, 37.3391, 127.0955)
            self.assertIsNone(result)

    @responses.activate
    def test_get_transit_routes_cached_on_second_call(self):
        """동일 요청은 캐싱됨"""
        responses.add(
            responses.GET,
            'https://api.odsay.com/v1/api/searchPubTransPathT',
            json={'result': {'path': []}},
            status=200
        )

        # 첫 번째 호출
        result1 = get_transit_routes(37.5712, 126.9258, 37.3391, 127.0955)

        # 두 번째 호출 (캐시에서)
        result2 = get_transit_routes(37.5712, 126.9258, 37.3391, 127.0955)

        # API 호출은 1번만 되어야 함
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(result1, result2)
