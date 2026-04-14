with open(r'apps/compliance/views.py', 'r') as f:
    c = f.read()

# Hapus duplikat import pertama yang lama
old = """from .serializers import (
    OJKIncidentSerializer, InformationBarrierSerializer, RemoteWipeSerializer,
    SecureFileLinkSerializer, DLPRuleSerializer, HelpdeskTicketSerializer,
    InstitutionBadgeSerializer,
)
from .serializers import ("""

new = "from .serializers import ("

c = c.replace(old, new, 1)

with open(r'apps/compliance/views.py', 'w') as f:
    f.write(c)

print("Done!")
