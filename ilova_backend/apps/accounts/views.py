from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from apps.accounts.models import PhoneToken
from apps.accounts.serializers import (
    PhoneTokenCreateSerializer, PhoneTokenValidateSerializer
)
from apps.accounts.utils import user_detail


class GenerateOTP(CreateAPIView):
    queryset = PhoneToken.objects.all()
    serializer_class = PhoneTokenCreateSerializer

    def post(self, request, format=None):
        ser = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        if ser.is_valid():
            token = PhoneToken.create_otp_for_number(
                request.data.get('phone_number')
            )
            if token:
                phone_token = self.serializer_class(
                    token, context={'request': request}
                )
                data = phone_token.data
                if getattr(settings, 'PHONE_LOGIN_DEBUG', False):
                    data['debug'] = token.otp
                return Response(data)
            return Response({
                'reason': "you can not have more than {n} attempts per day, please try again tomorrow".format(
                    n=getattr(settings, 'PHONE_LOGIN_ATTEMPTS', 10))}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


class ValidateOTP(CreateAPIView):
    queryset = PhoneToken.objects.all()
    serializer_class = PhoneTokenValidateSerializer

    def post(self, request, format=None):
        # Get the patient if present or result None.
        ser = self.serializer_class(
            data=request.data, context={'request': request}
        )
        if ser.is_valid():
            pk = request.data.get("pk")
            otp = request.data.get("otp")
            try:
                user = authenticate(request, pk=pk, otp=otp)
                if user:
                    last_login = user.last_login
                login(request, user)
                response = user_detail(user, last_login)
                return Response(response, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                return Response(
                    {'reason': "OTP doesn't exist"},
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )
        return Response(
            {'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
        

# test permission
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

class TestPermission(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return Response(
            {
                'message': 'You are authenticated.', 
                'user': request.user.id
            }
        )
