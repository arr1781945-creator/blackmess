with open(r'apps/workspace/serializers.py', 'r') as f:
    c = f.read()

c = c.replace(
    r'    display_name = serializers.CharField(source="user.display_name", read_only=True)',
    r'    display_name = serializers.SerializerMethodField()\n\n    def get_display_name(self, obj):\n        return obj.user.get_full_name() or obj.user.username'
)

with open(r'apps/workspace/serializers.py', 'w') as f:
    f.write(c)

print("Done!")
