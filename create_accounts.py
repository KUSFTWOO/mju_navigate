import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User

# Admin user
admin_user = User.objects.create_superuser(
    username='admin',
    email='admin@mju-navigate.kr',
    password='Admin@1234'
)
print("Created admin:", admin_user.username)

# Test user 1 - Seoul campus
user1 = User.objects.create_user(
    username='student_seoul',
    email='student.seoul@mju.kr',
    password='Student@1234'
)
user1.profile.campus = 'seoul'
user1.profile.nickname = 'Seoul Student'
user1.profile.save()
print("Created test user 1:", user1.username)

# Test user 2 - Yongin campus
user2 = User.objects.create_user(
    username='student_yongin',
    email='student.yongin@mju.kr',
    password='Student@1234'
)
user2.profile.campus = 'yongin'
user2.profile.nickname = 'Yongin Student'
user2.profile.save()
print("Created test user 2:", user2.username)

# Test user 3 - Both campus
user3 = User.objects.create_user(
    username='student_both',
    email='student.both@mju.kr',
    password='Student@1234'
)
user3.profile.campus = 'both'
user3.profile.nickname = 'Both Campus Student'
user3.profile.save()
print("Created test user 3:", user3.username)

print("\nAll accounts created successfully!")
print("\nAccount list:")
print("=" * 70)
for user in User.objects.all():
    role = 'ADMIN' if user.is_superuser else 'USER'
    campus = user.profile.campus if hasattr(user, 'profile') else 'N/A'
    print(f"  {user.username:20} | {user.email:30} | {role:5}")
print("=" * 70)
