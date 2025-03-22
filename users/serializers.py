from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role  # Add role to the token payload
        token['username'] = user.username  # Optionally add username
        token['email'] = user.email  # Optionally add email
        return token