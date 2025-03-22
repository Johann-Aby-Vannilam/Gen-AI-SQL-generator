from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import CustomTokenObtainPairSerializer
from .permissions import HasRole

# Register View
class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role', 'user')  # Default role is 'user'

        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username, email=email, password=password, role=role)
        return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)

# Login View
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful!',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'role': user.role  # Include role in the response
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

# Profile View
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, status=status.HTTP_200_OK)


    
from rest_framework.permissions import IsAuthenticated

class AdminView(APIView):
    permission_classes = [IsAuthenticated, HasRole(['admin'])]

    def get(self, request):
        return Response({'message': 'Welcome, Admin!'}, status=status.HTTP_200_OK)