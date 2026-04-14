with open(r'apps/compliance/views.py', 'r') as f:
    c = f.read()

c = c.replace(
    r'from .models import (',
    r'from .serializers import (\n    OJKIncidentSerializer, InformationBarrierSerializer, RemoteWipeSerializer,\n    SecureFileLinkSerializer, DLPRuleSerializer, HelpdeskTicketSerializer,\n    InstitutionBadgeSerializer,\n)\nfrom .models import (',
    1
)

fixes = [
    (r'class OJKIncidentViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class OJKIncidentViewSet(viewsets.ModelViewSet):\n    serializer_class = OJKIncidentSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class InformationBarrierViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class InformationBarrierViewSet(viewsets.ModelViewSet):\n    serializer_class = InformationBarrierSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class RemoteWipeViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class RemoteWipeViewSet(viewsets.ModelViewSet):\n    serializer_class = RemoteWipeSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class SecureFileLinkViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class SecureFileLinkViewSet(viewsets.ModelViewSet):\n    serializer_class = SecureFileLinkSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class DLPRuleViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class DLPRuleViewSet(viewsets.ModelViewSet):\n    serializer_class = DLPRuleSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class HelpdeskTicketViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class HelpdeskTicketViewSet(viewsets.ModelViewSet):\n    serializer_class = HelpdeskTicketSerializer\n    permission_classes = [IsAuthenticated]'),
    (r'class InstitutionBadgeViewSet(viewsets.ModelViewSet):\n    permission_classes = [IsAuthenticated]',
     r'class InstitutionBadgeViewSet(viewsets.ModelViewSet):\n    serializer_class = InstitutionBadgeSerializer\n    permission_classes = [IsAuthenticated]'),
]

for old, new in fixes:
    c = c.replace(old, new)

with open(r'apps/compliance/views.py', 'w') as f:
    f.write(c)

print("Done!")
