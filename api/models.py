"""
sync_app/models.py
──────────────────
Local mirror tables for PKTC SQL Anywhere data.
db_table names match the PKTC source table names exactly.
"""

from django.db import models


# ══════════════════════════════════════════════════════
#  Product  ←  acc_product
# ══════════════════════════════════════════════════════

class Product(models.Model):
    code      = models.CharField(max_length=30, primary_key=True)
    name      = models.CharField(max_length=200, blank=True, null=True)
    defected  = models.CharField(max_length=1,   blank=True, null=True)
    product   = models.CharField(max_length=30,  blank=True, null=True)
    brand     = models.CharField(max_length=30,  blank=True, null=True)
    company   = models.CharField(max_length=30,  blank=True, null=True)
    settings  = models.TextField(blank=True, null=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acc_product"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ══════════════════════════════════════════════════════
#  SyncUser  ←  acc_users  (role = '3')
# ══════════════════════════════════════════════════════

class SyncUser(models.Model):
    macc_id   = models.CharField(max_length=50, unique=True)   # acc_users.id  (e.g. "ARUN")
    pass_hash = models.CharField(max_length=200, blank=True, null=True)  # acc_users.pass
    role      = models.CharField(max_length=20, blank=True, null=True)   # e.g. "Level 3"
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acc_users"
        ordering = ["macc_id"]

    def __str__(self):
        return f"{self.macc_id} (role={self.role})"


# ══════════════════════════════════════════════════════
#  Firm  ←  misel  (single row)
# ══════════════════════════════════════════════════════

class Firm(models.Model):
    firm_name = models.CharField(max_length=150, blank=True, null=True)
    address   = models.CharField(max_length=40,  blank=True, null=True)
    mobile    = models.CharField(max_length=60,  blank=True, null=True)
    address1  = models.CharField(max_length=50,  blank=True, null=True)
    address2  = models.CharField(max_length=50,  blank=True, null=True)
    address3  = models.CharField(max_length=50,  blank=True, null=True)
    tinno     = models.CharField(max_length=30,  blank=True, null=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "misel"

    def __str__(self):
        return self.firm_name or "Firm"


# ══════════════════════════════════════════════════════
#  ProductPhoto  ←  acc_productphoto
# ══════════════════════════════════════════════════════

class ProductPhoto(models.Model):
    code      = models.CharField(max_length=30,  db_index=True)
    url2      = models.CharField(max_length=300, blank=True, null=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acc_productphoto"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.url2}"


# ══════════════════════════════════════════════════════
#  Customer  ←  acc_master  (super_code = 'DEBTO')
# ══════════════════════════════════════════════════════

class Customer(models.Model):
    code       = models.CharField(max_length=30,  primary_key=True)
    name       = models.CharField(max_length=250)
    super_code = models.CharField(max_length=5,   blank=True, null=True)
    phone2     = models.CharField(max_length=60,  blank=True, null=True)
    place      = models.CharField(max_length=60,  blank=True, null=True)
    city       = models.CharField(max_length=80,  blank=True, null=True)
    address    = models.CharField(max_length=100, blank=True, null=True)
    synced_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acc_master"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ══════════════════════════════════════════════════════
#  Ledger  ←  acc_ledgers  (DEBTO customers only)
#
#  Stores ledger entries for debtors (customers whose
#  acc_master.super_code = 'DEBTO').  The customer name
#  is denormalised here (customer_name) so the mobile
#  app never needs a second join.
#
#  Fields sourced from acc_ledgers:
#    accno, code, particulars, debit, credit,
#    entry_mode, date, voucher_no, narration
#
#  customer_name is resolved locally from acc_master
#  (super_code = 'DEBTO') and stored for convenience.
# ══════════════════════════════════════════════════════

class Ledger(models.Model):
    accno         = models.BigIntegerField(primary_key=True)   # acc_ledgers.accno  (PK in source)
    code          = models.CharField(max_length=30, db_index=True)   # acc_master.code (FK)
    customer_name = models.CharField(max_length=250, blank=True, null=True)  # denormalised from acc_master
    particulars   = models.CharField(max_length=250, blank=True, null=True)
    debit         = models.DecimalField(max_digits=15, decimal_places=5,
                                        blank=True, null=True)
    credit        = models.DecimalField(max_digits=15, decimal_places=5,
                                        blank=True, null=True)
    entry_mode    = models.CharField(max_length=30, blank=True, null=True)
    date          = models.DateField(blank=True, null=True)
    voucher_no    = models.BigIntegerField(blank=True, null=True)
    narration     = models.CharField(max_length=250, blank=True, null=True)
    synced_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acc_ledgers"
        ordering = ["code", "date", "accno"]

    def __str__(self):
        return f"{self.code} | {self.date} | debit={self.debit} credit={self.credit}"


# ══════════════════════════════════════════════════════
#  SyncLog  (audit trail — not in PKTC source DB)
# ══════════════════════════════════════════════════════

class SyncLog(models.Model):
    STATUS_CHOICES = [("ok", "OK"), ("error", "Error")]

    entity     = models.CharField(max_length=50)
    fetched    = models.IntegerField(default=0)
    pushed     = models.IntegerField(default=0)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ok")
    error_msg  = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    duration_s = models.FloatField(default=0.0)

    class Meta:
        db_table = "sync_log"
        ordering = ["-started_at"]

    def __str__(self):
        return f"[{self.started_at:%Y-%m-%d %H:%M}] {self.entity} — {self.status}"