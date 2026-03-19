import random
import string
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .email_service import send_otp_email, send_invite_email

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data.get('email')
    name = request.data.get('name', '')
    if not email:
        return Response({'error': 'Email required'}, status=400)
    otp = generate_otp()
    cache.set(f'otp_{email}', otp, timeout=600)
    sent = send_otp_email(email, otp, name)
    if sent:
        return Response({'message': 'OTP sent'})
    return Response({'error': 'Failed to send email'}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    if not email or not otp:
        return Response({'error': 'Email and OTP required'}, status=400)
    cached_otp = cache.get(f'otp_{email}')
    if not cached_otp:
        return Response({'error': 'OTP expired'}, status=400)
    if cached_otp != otp:
        return Response({'error': 'OTP invalid'}, status=400)
    cache.delete(f'otp_{email}')
    return Response({'message': 'OTP verified'})

@api_view(['POST'])
@permission_classes([AllowAny])
def send_invite(request):
    to_email = request.data.get('to_email')
    from_name = request.data.get('from_name')
    invite_link = request.data.get('invite_link')
    workspace = request.data.get('workspace', 'BlackMess')
    if not all([to_email, from_name, invite_link]):
        return Response({'error': 'Missing fields'}, status=400)
    sent = send_invite_email(to_email, from_name, invite_link, workspace)
    if sent:
        return Response({'message': 'Invite sent'})
    return Response({'error': 'Failed to send email'}, status=500)
