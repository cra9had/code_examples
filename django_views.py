import hashlib
import hmac
from .models import Transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.models import User
from .serializers import BuySearchesSerializer
from search_base.models import SearchHistory
from django.conf import settings
from .utils import buy_full_data, get_payment_url, add_searches_to_user


class PayOkPaymentAPIView(APIView):
    permission_classes = [AllowAny, ]

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def post(self, request):
        if self.get_client_ip() in ['195.64.101.191', '194.124.49.173', '45.8.156.144', '5.180.194.179',
                                    '5.180.194.127', '2a0b:1580:5ad7:0dea:de47:10ae:ecbf:111a']:    # From Payok servers
            data = request.POST
            trx_pk = int(data.get("payment_id"))
            amount = data.get("amount")
            desc = data.get("desc")
            currency = data.get("currency")
            shop = data.get("shop")
            sign = hashlib.md5(
                f"{settings.PAYOK_API_KEY}|{desc}|{currency}|{shop}|{trx_pk}|{amount}".encode('utf-8')).hexdigest()
            if sign != data.get("sign"):    # Not correct signature
                return Response(status=status.HTTP_404_NOT_FOUND)

            trx = Transaction.objects.get(pk=trx_pk)
            add_searches_to_user(trx)
            return Response({"content": "ok"}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class OxaPayPaymentAPIView(APIView):
    """Payment webhook"""
    permission_classes = [AllowAny, ]

    def post(self, request):
        raw_data = request.body
        data = request.data
        if not data.get("type", "") == "payment":
            return Response(status=status.HTTP_404_NOT_FOUND)
        hmac_header = request.headers.get('HMAC')
        calculated_hmac = hmac.new(settings.OXAPAY_API_KEY.encode(), raw_data, hashlib.sha512).hexdigest()
        if calculated_hmac == hmac_header:
            trx_pk = int(data.get("orderId"))
            if data.get("status") == "Expired":
                Transaction.objects.get(pk=trx_pk).delete()
            elif data.get("status") == "Paid":
                trx = Transaction.objects.get(pk=trx_pk)
                add_searches_to_user(trx)
            return Response({"content": "ok"}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class BuySearchesAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        serializer = BuySearchesSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        trx = serializer.save()
        payment_detail = get_payment_url(trx.amount, trx.pk, trx.top_up_method)
        return Response(payment_detail, status=status.HTTP_200_OK)


class BuyFullDataAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get_object(self, pk):
        try:
            return SearchHistory.objects.get(pk=pk, user=self.request.user)
        except SearchHistory.DoesNotExist:
            raise

    def post(self, request):
        try:
            search = self.get_object(request.data.get("pk"))
        except SearchHistory.DoesNotExist:
            return Response({"error": "Search does not exist"}, status=status.HTTP_404_NOT_FOUND)
        if search.status != 2:
            return Response({"error": "Search status is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        if self.request.user.available_searches <= 0:
            return Response({"error": "Приобретите пробивы\nв меню!"}, status=status.HTTP_400_BAD_REQUEST)
        if search.paid:
            return Response({"error": "Данные уже куплены!"}, status=status.HTTP_400_BAD_REQUEST)
        full_data = buy_full_data(self.request.user, search)
        return Response({"available_searches": self.request.user.available_searches, "result": full_data}, status=status.HTTP_200_OK)


class GetBonusAPIView(APIView):
    """
    Add a free bonus for user if not used yet
    """
    def get(self, request, telegram_id):
        if self.request.user.telegram_id or User.objects.filter(telegram_id=telegram_id).exists() or self.request.user.bonus_used:
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.request.user.telegram_id = telegram_id
        self.request.user.bonus_used = True
        self.request.user.available_searches += 1
        self.request.user.save()
        return Response(status=status.HTTP_200_OK)
