from django.test import TestCase, Client
from django.urls import reverse
import responses


class NavigationViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_navigation_index_200(self):
        """메인 페이지 로드 성공"""
        response = self.client.get(reverse('navigation:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'navigation/index.html')

    @responses.activate
    def test_route_search_returns_partial_html(self):
        """경로 검색 시 partial HTML 반환"""
        responses.add(
            responses.GET,
            'https://api.odsay.com/v1/api/searchPubTransPathT',
            json={
                'result': {
                    'path': [
                        {
                            'totalTime': 45,
                            'fare': 1250,
                        }
                    ]
                }
            },
            status=200
        )

        response = self.client.get(
            reverse('navigation:search'),
            {
                'origin': 'seoul_campus',
                'destination': 'yongin_campus',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'navigation/partials/route_results.html')

    def test_route_search_api_fail_returns_error_partial(self):
        """API 실패 시 에러 partial 반환"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                'https://api.odsay.com/v1/api/searchPubTransPathT',
                status=500
            )

            response = self.client.get(
                reverse('navigation:search'),
                {
                    'origin': 'seoul_campus',
                    'destination': 'yongin_campus',
                }
            )

            self.assertEqual(response.status_code, 400)
            self.assertTemplateUsed(response, 'navigation/partials/route_error.html')
