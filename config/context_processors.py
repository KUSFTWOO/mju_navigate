from django.conf import settings


def kakao_api_keys(request):
    """Kakao API 키를 템플릿 context에 추가"""
    return {
        'KAKAO_API_KEY': settings.KAKAO_API_KEY,
        'KAKAO_JS_KEY': settings.KAKAO_JS_KEY,
        'ODSAY_API_KEY': settings.ODSAY_API_KEY,
    }
