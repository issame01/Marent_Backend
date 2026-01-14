from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext as _
import logging
from .models import Listing, ListingImage
from .serializers import ListingSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

logger = logging.getLogger(__name__)


class ListingCreateView(generics.CreateAPIView):
    serializer_class = ListingSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        listing = serializer.save(seller=self.request.user)
        # Handle multiple images
        images = self.request.FILES.getlist('images')
        for index, image in enumerate(images):
            ListingImage.objects.create(
                listing=listing,
                image=image,
                is_primary=(index == 0)  # first image = primary
            )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Log the payload (optional)
        logger.info(_('Listing creation payload: %s'), request.data)
        
        # Create the listing
        self.perform_create(serializer)
        
        # Prepare response
        response_data = {
            "data": serializer.data,
            "message": _("Listing published successfully"),
            "listing_id": serializer.instance.id
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

class ListingListView(generics.ListAPIView):
    """View for listing all available listings"""
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]  # Anyone can view listings
    queryset = Listing.objects.filter(availability=True).select_related('seller')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add filters if needed
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
            
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # print(list(queryset.values(
        #     'id', 'title', 'price', 'category', 'location', 'seller',
        #     )))

        return queryset

class ListingDetailView(generics.RetrieveAPIView):
    """View for retrieving a single listing"""
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]
    queryset = Listing.objects.all().select_related('seller')
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        # instance.views += 1
        # instance.save(update_fields=['views'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ListingUpdateView(generics.UpdateAPIView):
    """View for updating a listing (only by owner)"""
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Listing.objects.all()
    lookup_field = 'id'
    
    def get_queryset(self):
        # Users can only update their own listings
        return Listing.objects.filter(seller=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(_('Listing updated: %s'), serializer.instance.id)

class ListingDeleteView(generics.DestroyAPIView):
    """View for deleting a listing (only by owner)"""
    permission_classes = [IsAuthenticated]
    queryset = Listing.objects.all()
    lookup_field = 'id'
    
    def get_queryset(self):
        # Users can only delete their own listings
        return Listing.objects.filter(seller=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": _("Listing deleted successfully")},
            status=status.HTTP_204_NO_CONTENT
        )