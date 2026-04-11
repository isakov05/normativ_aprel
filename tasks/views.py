from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from tasks.models import Tasks
from tasks.serializers import TasksSerializer
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permission import IsOwnerOrReadOnly

@api_view(['GET'])
def test_api(request):
    return Response({
        "message": "Hello DRF"
    })


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Tasks.objects.select_related('author').all().order_by('-created_at')
    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]

    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    filterset_fields = ['title']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RegisterAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not username or not password:
            return Response({'error': 'Username va password kerak'}, status=400)

        if password != confirm_password:
            return Response({'error': 'Passwordlar mos emas'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'User mavjud'}, status=400)

        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()

        return Response({'message': 'User created'}, status=201)


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid username or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        return Response({'message': 'Logged in'})


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out'})