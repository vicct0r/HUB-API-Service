from django.shortcuts import render, get_object_or_404
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import DistributionCenter
from .serializers import CdSerializer, CdInfoSerializer
from .utils.check_conn import cd_running
from .utils.trade_op import gatherAvailableCDs
from .utils.transactions import buy_endpoint, sell_endpoint

import requests

class CdRegisterAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CdSerializer(data=request.data)

        if serializer.is_valid():
            cd = serializer.save()
            if cd_running(cd_url=cd.url):
                cd.status = True
                cd.save()

            return Response({
                "status": "success",
                "message": "CD has been added to the HUB database.",
                "CD name": cd.name,
                "CD conn status": cd.status
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": "Something went wrong.",
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class CdGatherInfoAPIView(APIView):
    def get(self, request, *args, **kwargs):
        cd = kwargs.get('cd_name')

        if cd:
            dc = DistributionCenter.objects.filter(name=cd)
        else:
            dc = DistributionCenter.objects.all()

        serializer = CdSerializer(dc, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CdRequestTradeAPIView(APIView):
    def post(self, request, *args, **kwargs):
        product = kwargs.get('product')
        quantity = int(kwargs.get('quantity'))

        if not product or not quantity:
            return Response({
                "status": "error",
                "message": "Please provide the product and quantity required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cds = DistributionCenter.objects.filter(is_active=True)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR") # verificando se o IP vem de um Load Balancer/Proxy

        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]  # pega o primeiro IP da cadeia
        else:
            ip = request.META.get("REMOTE_ADDR")
        
        formated_cd_url = f"http://{ip}/cd/v1/"
        selected_cd = None
        distribution_centers = []

        for cd in cds:
            if cd.url == formated_cd_url:
                continue

            try:
                response = requests.get(url=f"{cd.url}product/request/{product}/{quantity}/", timeout=5)
                response.raise_for_status()
            except Exception as e:
                continue

            distribution_centers.append(cd.name)
            
            if response.json()['available']:
                if selected_cd:
                    if response.json()['price'] < selected_cd['price']:
                        selected_cd = {"price": response.json()['price'], "available": response.json()['available'], "cd": cd}
                else:
                    selected_cd = {"price": response.json()['price'], "available": response.json()['available'], "cd": cd}

        if not selected_cd:
            return Response({
                "status": "error",
                "message": "Product not found on the CDs! Contact the HUB!"
            }, status=status.HTTP_404_NOT_FOUND)
        
        target_transaction_cd = get_object_or_404(DistributionCenter, name=selected_cd["name"])
        requested_transaction_cd = get_object_or_404(DistributionCenter, url=formated_cd_url)
        
        if not cd_running(target_transaction_cd) and not cd_running(requested_transaction_cd):
            return Response({
                "status": "error",
                "message": "Transaction aborted due to connection error.",
                "seller_cd_conn": cd_running(target_transaction_cd),
                "client_cd_conn": cd_running(requested_transaction_cd),
                "targets": distribution_centers
            }, status=status.HTTP_424_FAILED_DEPENDENCY)
        
        if buy_endpoint(cd_url=requested_transaction_cd, product=product, quantity=quantity) and sell_endpoint(cd_url=target_transaction_cd, product=product, quantity=quantity):
            with transaction.atomic():
                target_transaction_cd.balance += selected_cd["price"]
                requested_transaction_cd.balance -= selected_cd["price"]
                target_transaction_cd.save()
                requested_transaction_cd.save()
            
            return Response({
            "status": "success",
            "message": f"The CD {requested_transaction_cd.name} bought {quantity} {product}'s from the {target_transaction_cd.name}!",
            "action": "trade"
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "The transaction failed due to server error with the Distribution Center!"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    





            
            
            
