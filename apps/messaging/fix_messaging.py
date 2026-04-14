with open(r'apps/messaging/views.py', 'r') as f:
    c = f.read()

c = c.replace(
    r'class MessageListView(generics.ListCreateAPIView):\n    serializer_class = MessageSerializer\n    serializer_class = MessageSerializer\n    permission_classes = [permissions.IsAuthenticated]',
    r'class MessageListView(generics.ListCreateAPIView):\n    permission_classes = [permissions.IsAuthenticated]\n\n    def get_serializer_class(self):\n        if self.request.method == "POST":\n            from .serializers import MessageCreateSerializer\n            return MessageCreateSerializer\n        return MessageSerializer'
)

with open(r'apps/messaging/views.py', 'w') as f:
    f.write(c)

print("Done!")
