import uuid
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    email_id = models.EmailField()
    annual_income = models.FloatField()
    aadhar_id = models.CharField(max_length=255, unique=True)
    credit_score = models.IntegerField(null=True, blank=True)
    user_id = models.UUIDField(default=uuid.uuid4, unique=True)

class Loan(models.Model):
    loan_id = models.UUIDField(default=uuid.uuid4, unique=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, to_field='user_id')
    loan_type = models.CharField(max_length=255)
    loan_amount = models.IntegerField(default=0)
    interest_rate = models.FloatField()
    term_period = models.IntegerField(default=0)
    disbursement_date = models.DateField()
    
class Billing(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, to_field='loan_id')
    billing_date = models.DateField()
    due_date = models.DateField()
    min_due = models.DecimalField(max_digits=10, decimal_places=2)
    principal_due = models.DecimalField(max_digits=10, decimal_places=2)
    interest_due = models.DecimalField(max_digits=10, decimal_places=2)
    
class DuePayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, to_field='loan_id')
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    
class Payment(models.Model):
    loan_id = models.ForeignKey(Loan, on_delete=models.CASCADE, to_field='loan_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)