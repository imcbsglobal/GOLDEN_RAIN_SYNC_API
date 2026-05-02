"""
api/urls.py
───────────
Included from backend/urls.py as:  path("api/", include("api.urls"))

Full URL table:
  GET   /api/sync/products/       → list local acc_product
  POST  /api/sync/products/       → upsert into local acc_product

  GET   /api/sync/users/          → list local acc_users
  POST  /api/sync/users/          → upsert into local acc_users

  GET   /api/sync/firm/           → get local misel
  POST  /api/sync/firm/           → upsert into local misel

  GET   /api/sync/product-photos/ → list local acc_productphoto
  POST  /api/sync/product-photos/ → replace in local acc_productphoto

  GET   /api/sync/customers/      → list local acc_master
  POST  /api/sync/customers/      → upsert into local acc_master

  GET   /api/sync/all/            → full data dump
  GET   /api/sync/logs/           → last 100 sync log entries
"""

from django.urls import path
from .views import (
    ProductListView,
    UserListView,
    FirmView,
    ProductPhotoListView,
    CustomerListView,
    FullSyncView,
    SyncLogView,
)

urlpatterns = [
    path("sync/products/",       ProductListView.as_view(),      name="sync-products"),
    path("sync/users/",          UserListView.as_view(),         name="sync-users"),
    path("sync/firm/",           FirmView.as_view(),             name="sync-firm"),
    path("sync/product-photos/", ProductPhotoListView.as_view(), name="sync-product-photos"),
    path("sync/customers/",      CustomerListView.as_view(),     name="sync-customers"),
    path("sync/all/",            FullSyncView.as_view(),         name="sync-all"),
    path("sync/logs/",           SyncLogView.as_view(),          name="sync-logs"),
]