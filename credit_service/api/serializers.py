from rest_framework import serializers
from .models import User, Loan, Payment

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['name', 'annual_income', 'aadhar_id', 'user_id', 'email_id']

class LoanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Loan
        fields = ['user_id', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date']

class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['loan_id', 'amount']