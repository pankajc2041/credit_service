from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta, datetime
from .models import Billing
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class LoanProcessor:
    def __init__(self, loan_amount, interest_rate, term_period, billing_date, user):
        self.loan_amount = Decimal(loan_amount)
        self.interest_rate = Decimal(interest_rate)
        self.term_period = int(term_period)
        self.billing_date = billing_date
        self.monthly_interest_rate = self.interest_rate / Decimal('12') / Decimal('100')
        self.emi = self.calculate_emi(self.loan_amount, self.term_period)
        self.due_dates = self.emi_schedule(self.loan_amount, self.term_period, self.interest_rate, self.billing_date, user)
        
    def calculate_emi(self, loan_amount, term_period):
        loan_amount = loan_amount
        term_period = term_period
        emi = self.loan_amount * self.monthly_interest_rate * ((1 + self.monthly_interest_rate) ** self.term_period) / (((1 + self.monthly_interest_rate) ** self.term_period) - 1)
        return emi.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    
    def emi_schedule(self,loan_amount, term_period, interest_rate, billing_date, user):
        due_dates = []
        principal_balance = loan_amount
        
        for i in range(term_period):
            due_date = billing_date + timedelta(days=30*i)
            daily_apr = round(Decimal(interest_rate) / Decimal('365'), 3)
            interest = daily_apr * principal_balance * Decimal('30') / Decimal('100')
            if interest < 50:
                return -1
            min_due = self.emi
            
            if i == term_period - 1:
                min_due = principal_balance + interest
                
            
                
            due_dates.append({
                "due_date": due_date,
                "min_due": float(min_due),
                "principal_due": float(principal_balance / term_period),
                "interest": float(interest),
            })
            
            principal_balance -= self.emi - interest
        
        return due_dates
    
    
def setup_periodic_tasks():
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.DAYS,
    )

    PeriodicTask.objects.create(
        interval=schedule,
        name='Daily Billing Task',
        task='api.tasks.process_billing',
        args=json.dumps([]),
    )