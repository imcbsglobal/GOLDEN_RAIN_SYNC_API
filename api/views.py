"""
api/views.py
────────────
GET  → return local mirrored data from Django ORM
POST → receive records from sync.py and upsert into local Django DB

No JWT required — uses AllowAny (set in settings.py REST_FRAMEWORK).
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Product, SyncUser, Firm, ProductPhoto, Customer, SyncLog

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════

def _bad(msg):
    return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


def _log(entity, fetched, pushed, status_val="ok", error=""):
    try:
        SyncLog.objects.create(
            entity=entity, fetched=fetched, pushed=pushed,
            status=status_val, error_msg=error or None,
        )
    except Exception as exc:
        logger.warning("Could not write SyncLog: %s", exc)


# ══════════════════════════════════════════════════════
#  PRODUCTS   /api/sync/products/
# ══════════════════════════════════════════════════════

class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = Product.objects.all().values(
            "code", "name", "defected", "product", "brand", "company"
        )
        return Response({"count": len(products), "results": list(products)})

    def post(self, request):
        """Payload: [ {code, name, defected, product, brand, company}, ... ]"""
        payload = request.data
        if not isinstance(payload, list):
            return _bad("Expected a JSON array.")

        errors = 0
        objs = []
        for item in payload:
            code = (item.get("code") or "").strip()
            if not code:
                errors += 1
                continue
            objs.append(Product(
                code=code,
                name=item.get("name"),
                defected=item.get("defected"),
                product=item.get("product"),
                brand=item.get("brand"),
                company=item.get("company"),
            ))

        Product.objects.bulk_create(
            objs,
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=["name", "defected", "product", "brand", "company", "synced_at"],
        )

        _log("products", len(payload), len(objs))
        return Response({
            "received": len(payload), "saved": len(objs),
            "errors": errors, "status": "ok",
        })


# ══════════════════════════════════════════════════════
#  USERS   /api/sync/users/
# ══════════════════════════════════════════════════════

class UserListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        users = SyncUser.objects.all().values("macc_id", "pass_hash", "role")
        return Response({"count": len(users), "results": list(users)})

    def post(self, request):
        """Payload: [ {id, pass, role}, ... ]
        id   → macc_id  (e.g. 'ARUN', 'SAJITH')
        pass → pass_hash (plain text from SQL Anywhere)
        role → role      (e.g. 'Level 3')
        """
        payload = request.data
        if not isinstance(payload, list):
            return _bad("Expected a JSON array.")

        errors = 0
        objs = []
        for item in payload:
            macc_id = (item.get("id") or "").strip()
            if not macc_id:
                errors += 1
                continue
            objs.append(SyncUser(
                macc_id=macc_id,
                pass_hash=item.get("pass") or "",   # pass can be NULL in source
                role=item.get("role"),
            ))

        SyncUser.objects.bulk_create(
            objs,
            update_conflicts=True,
            unique_fields=["macc_id"],
            update_fields=["pass_hash", "role", "synced_at"],
        )

        _log("users", len(payload), len(objs))
        return Response({
            "received": len(payload), "saved": len(objs),
            "errors": errors, "status": "ok",
        })


# ══════════════════════════════════════════════════════
#  FIRM   /api/sync/firm/
# ══════════════════════════════════════════════════════

class FirmView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        firm = Firm.objects.first()
        if not firm:
            return Response({})
        return Response({
            "firm_name": firm.firm_name,
            "address":   firm.address,
            "mobile":    firm.mobile,
            "address1":  firm.address1,
            "address2":  firm.address2,
            "address3":  firm.address3,
            "tinno":     firm.tinno,
        })

    def post(self, request):
        """Payload: {firm_name, address, mobile, address1, address2, address3, tinno}"""
        payload = request.data
        if not isinstance(payload, dict):
            return _bad("Expected a JSON object.")

        Firm.objects.update_or_create(
            pk=1,
            defaults={
                "firm_name": payload.get("firm_name"),
                "address":   payload.get("address"),
                "mobile":    payload.get("mobile"),
                "address1":  payload.get("address1"),
                "address2":  payload.get("address2"),
                "address3":  payload.get("address3"),
                "tinno":     payload.get("tinno"),
            },
        )
        _log("firm", 1, 1)
        return Response({"received": 1, "status": "ok"})


# ══════════════════════════════════════════════════════
#  PRODUCT PHOTOS   /api/sync/product-photos/
# ══════════════════════════════════════════════════════

class ProductPhotoListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        photos = ProductPhoto.objects.all().values("code", "url2")
        return Response({"count": len(photos), "results": list(photos)})

    def post(self, request):
        """Payload: [ {code, url2}, ... ]"""
        payload = request.data
        if not isinstance(payload, list):
            return _bad("Expected a JSON array.")

        codes = {item.get("code") for item in payload if item.get("code")}
        ProductPhoto.objects.filter(code__in=codes).delete()

        objs = [
            ProductPhoto(code=item["code"], url2=item.get("url2"))
            for item in payload if item.get("code")
        ]
        ProductPhoto.objects.bulk_create(objs)

        _log("product_photos", len(payload), len(objs))
        return Response({"received": len(payload), "saved": len(objs), "status": "ok"})


# ══════════════════════════════════════════════════════
#  CUSTOMERS   /api/sync/customers/
# ══════════════════════════════════════════════════════

class CustomerListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        customers = Customer.objects.filter(super_code="DEBTO").values(
            "code", "name", "super_code", "phone2", "place", "city", "address"
        )
        return Response({"count": len(customers), "results": list(customers)})

    def post(self, request):
        """Payload: [ {code, name, super_code, phone2, place, city, address}, ... ]"""
        payload = request.data
        if not isinstance(payload, list):
            return _bad("Expected a JSON array.")

        errors = 0
        objs = []
        for item in payload:
            code = (item.get("code") or "").strip()
            name = (item.get("name") or "").strip()
            if not code or not name:
                errors += 1
                continue
            objs.append(Customer(
                code=code,
                name=name,
                super_code=item.get("super_code"),
                phone2=item.get("phone2"),
                place=item.get("place"),
                city=item.get("city"),
                address=item.get("address"),
            ))

        Customer.objects.bulk_create(
            objs,
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=["name", "super_code", "phone2", "place", "city", "address", "synced_at"],
        )

        _log("customers", len(payload), len(objs))
        return Response({
            "received": len(payload), "saved": len(objs),
            "errors": errors, "status": "ok",
        })


# ══════════════════════════════════════════════════════
#  FULL SYNC   /api/sync/all/
# ══════════════════════════════════════════════════════

class FullSyncView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "products":      list(Product.objects.all().values()),
            "users":         list(SyncUser.objects.all().values()),
            "firm":          Firm.objects.first().__dict__ if Firm.objects.exists() else {},
            "product_photos": list(ProductPhoto.objects.all().values()),
            "customers":     list(Customer.objects.all().values()),
        }
        # remove _state key from firm dict if present
        data["firm"].pop("_state", None)
        summary = {k: len(v) if isinstance(v, list) else 1 for k, v in data.items()}
        return Response({"summary": summary, "data": data})


# ══════════════════════════════════════════════════════
#  SYNC LOGS   /api/sync/logs/
# ══════════════════════════════════════════════════════

class SyncLogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logs = SyncLog.objects.order_by("-started_at")[:100].values(
            "id", "entity", "fetched", "pushed",
            "status", "error_msg", "started_at", "duration_s",
        )
        return Response({"count": len(logs), "results": list(logs)})