from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView
from .views import ListingCreateView, ListingListView, ListingDetailView, ListingUpdateView, ListingDeleteView
urlpatterns = [
    path('listings/', ListingListView.as_view(), name='listing-list'),
    path('listings/create/', ListingCreateView.as_view(), name='listing-create'),
    path('listings/<int:id>/', ListingDetailView.as_view(), name='listing-detail'),
    path('listings/<int:id>/update/', ListingUpdateView.as_view(), name='listing-update'),
    path('listings/<int:id>/delete/', ListingDeleteView.as_view(), name='listing-delete'),
]
