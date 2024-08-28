import jwt
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from backend.settings import SECRET_KEY

from .common import check_authority
from ..serializers import *     # model도 포함


class TableAPIView(APIView):
    def get(self, request, booth_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            cached_data = cache.get(temporary_user_id)
            if not cached_data:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            loaded_booth_id = cached_data.get('booth_id')

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        user_instance = get_object_or_404(User, pk=loaded_booth_id)    # email로 user 정보가 있는지 확인
        table_items = Table.objects.filter(email=booth_id)
        serializer = TableSerializer(instance=table_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, booth_id):
        if check_authority(request, booth_id):
            user_instance = get_object_or_404(User, pk=booth_id)
            serializer = TableSerializer(data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.create(dict({'email': user_instance}, **request.data))
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            Response({"message":"자신의 부스에만 테이블을 추가할 수 있습니다"}, status=status.HTTP_204_NO_CONTENT)


class TableDetailAPIVIew(APIView):
    def get(self, request, booth_id, table_id):
        access_token = request.headers.get('Authorization', None)
        if access_token:
            access_token = access_token.replace('Bearer ', '')
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])  # 토큰 유효 확인
            loaded_booth_id = payload['email']  # 이메일 값
        else:
            temporary_user_id = request.COOKIES.get('temporary_user_id')
            if not temporary_user_id:
                return Response({"message": "인증키가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            cached_data = cache.get(temporary_user_id)
            if not cached_data:
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            loaded_booth_id = cached_data.get('booth_id')

        if not booth_id == loaded_booth_id:
            return Response({"message": "권한이 없는 부스 입니다."}, status=status.HTTP_403_FORBIDDEN)

        table_instance = get_object_or_404(Table, pk=table_id)
        serializer = TableSerializer(instance=table_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, booth_id, table_id):
        if check_authority(request, booth_id):
            table_instance = get_object_or_404(Table, pk=table_id)
            serializer = TableSerializer(instance=table_instance, data=dict({'email': booth_id}, **request.data))
            if serializer.is_valid(raise_exception=True):
                serializer.save(instance=table_instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                Response({"message": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "권한이 없습니다. 본인 부스의 테이블 정보만 바꿀 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, booth_id, table_id):
        if check_authority(request, booth_id):
            if Table.objects.count() <= 1 :
                return Response({"message": "테이블은 1개 이상 있어야 합니다"}, status = status.HTTP_409_CONFLICT)
            else :
                table_delete_instance = get_object_or_404(Table, pk=table_id)
                table_delete_instance.delete()
                return Response(status = status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "권한이 없습니다. 본인 부스의 테이블만 삭제할 수 있습니다."}, status=status.HTTP_401_UNAUTHORIZED)
