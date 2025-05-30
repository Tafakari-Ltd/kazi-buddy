from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser
from assignments.models import Assignment
from workers.models import WorkerProfile
from employers.models import EmployerProfile
# Create your models here.
class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    METHOD_TYPE_CHOICES = [
        ('mpesa', 'Mpesa'),
        ('bank_account', 'Bank Account'),
        ('card', 'Card'),
        ('airtel_money', 'Airtel Money'),
    ]
    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES)
    account_details = JSONField()
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method_type} - {self.user}"

class EscrowAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('funded', 'Funded'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    funded_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Escrow {self.id} - {self.status}"

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True)
    escrow_account = models.ForeignKey(EscrowAccount, on_delete=models.SET_NULL, null=True, blank=True)
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('fee', 'Fee'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'Mpesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('airtel_money', 'Airtel Money'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    external_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    reference_number = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.status}"