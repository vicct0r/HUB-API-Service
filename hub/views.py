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

        if product is None or quantity is None:
            return Response({
                "status": "error",
                "message": "Please provide the product and quantity required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cds = DistributionCenter.objects.filter(is_active=True)
        selected_cd = None
        distribution_centers = []
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR") # verificando se o IP vem de um Load Balancer/Proxy

        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]  # primeiro IP da cadeia
        else:
            ip = request.META.get("REMOTE_ADDR")
            port = request.META.get("REMOTE_PORT")
        
        url = f"http://{ip}:{port}/cd/v1/"

        for cd in cds:
            if cd.ip == ip:
                continue

            try:
                response = requests.get(url=f"{url}product/request/{product}/{quantity}/", timeout=5)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return Response({
                    "status": "error",
                    "message": "Failed to communicate with external service!",
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
    
            distribution_centers.append(cd.name)
            
            if not response.json()['available']:
                continue

            if selected_cd:
                if response.json()['price'] < selected_cd['price']:
                    selected_cd = {"price": response.json()['price'], "available": response.json()['available'], "cd": cd.name}
            else:
                    selected_cd = {"price": response.json()['price'], "available": response.json()['available'], "cd": cd.name}

        if not selected_cd:
            return Response({
                "status": "error",
                "message": f"No CD has the product {product}!"
            }, status=status.HTTP_404_NOT_FOUND)

        supplier_cd = get_object_or_404(DistributionCenter, name=selected_cd["cd"])
        buyer_cd = get_object_or_404(DistributionCenter, ip=ip)
        target_url = f"http://{supplier_cd.ip}/cd/v1/"
        try:
            t_response = requests.get(url=f"{target_url}info/", timeout=5)
            r_response = requests.get(url=f"{url}/info/", timeout=5)
            r_response.raise_for_status()
            t_response.raise_for_status()
        except Exception as e:
            return Response({
                "status": "error",
                "message": "Failed to communicate with external service!",
                "error": str(e)
            }, status=status.HTTP_424_FAILED_DEPENDENCY)
        
        if t_response.status_code == 200 and r_response.status_code == 200:
            buying_product = f"{url}product/buy/{product}/{quantity}/"
            selling_product = f"{target_url}product/sell/{product}/{quantity}/"
            buy_transaction = None
            sell_transaction = None

            try:
                buy_transaction = requests.post(url=buying_product, timeout=5)
                sell_transaction = requests.post(url=selling_product, timeout=5)
                buy_transaction.raise_for_status()
                sell_transaction.raise_for_status()
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": "Error during transaction between the Distribution Centers!",
                    "buyer_status_code": buy_transaction.status_code,
                    "supplier_status_code": sell_transaction.status_code,
                    "action": "failed"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            bought_product_price = selected_cd['price']
            
            return Response({
                "status": "success",
                "buyer": buyer_cd.name,
                "supplier": supplier_cd.name,
                "product": product,
                "quantity": quantity,
                "unit_price": bought_product_price,
                "total": bought_product_price * quantity,
                "action": "transaction"
            }, status=status.HTTP_200_OK)
            
            
