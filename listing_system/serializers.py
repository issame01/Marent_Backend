from rest_framework import serializers
from .models import Listing, ListingImage
from authentication.models import User



class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'is_primary']

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # or your Seller model
        fields = ('id', 'username', 'first_name', 'last_name', 'picture', 'email', 'created_at')  # choose fields

class ListingSerializer(serializers.ModelSerializer):
    seller = SellerSerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'category', 'description', 'condition', 'brand',
            'price', 'location', 'availability', 'seller', 'created_at', 
            'updated_at', 'price_type', 'rent_period', 'images',
        ]
        read_only_fields = ['seller', 'views', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        price_type = attrs.get('price_type', 'sale')
        rent_period = attrs.get('rent_period')
        
        # If price_type is 'rent', rent_period is required
        if price_type == 'rent' and not rent_period:
            raise serializers.ValidationError({'rent_period': 'Rent period is required when price type is rent'})
        # If price_type is 'sale', rent_period should be null
        if price_type == 'sale' and rent_period:
            attrs['rent_period'] = None
        return attrs

    def validate_price_type(self, value):
        valid_types = ['sale', 'rent']
        if value not in valid_types:
            raise serializers.ValidationError(f'Price type must be one of: {", ".join(valid_types)}')
        return value

    def validate_rent_period(self, value):
        if value:
            valid_periods = ['daily', 'weekly', 'monthly', 'yearly']
            if value not in valid_periods:
                raise serializers.ValidationError(f'Rent period must be one of: {", ".join(valid_periods)}')
        return value
        
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value