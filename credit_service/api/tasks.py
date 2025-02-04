from celery import shared_task
from .models import User, DuePayment, Billing
from django.conf import settings
import pandas as pd
import os
from datetime import datetime, timedelta
from django.db import transaction


@shared_task
def calculate_credit_score(user_id):
    
    user = User.objects.get(user_id=user_id)
    
    file_path = os.path.join(settings.BASE_DIR,'data', "transactions_data_backend__1_.csv")
    df = pd.read_csv(file_path)
    print("Here")
    user_transactions = df[df["user"] == user.aadhar_id]
    
    balance = user_transactions[user_transactions["transaction_type"] == "CREDIT"]["amount"].sum() - \
              user_transactions[user_transactions["transaction_type"] == "DEBIT"]["amount"].sum()
              
    if balance >= 1000000:
        credit_score = 900
    elif balance <= 100000:
        credit_score = 300
    else:
        credit_score = int(min(900, 300 + (balance - 100000) // 15000 * 10))
        
    user.credit_score = credit_score
    user.save()
        
@shared_task
def process_billing():
    today = datetime.today().date()
    users_to_bill = Billing.objects.filter(billing_date=today)
    
    for billing in users_to_bill:
        with transaction.atomic():
            user = billing.user
            min_due = billing.min_due
            due_payment = DuePayment.objects.create(
                user=user,
                amount_due=min_due,
                due_date=billing.due_date,
                paid=False
            )
            due_payment.save()
