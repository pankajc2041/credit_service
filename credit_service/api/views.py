from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Loan, Billing, DuePayment, Payment
from .serializers import UserSerializer, LoanSerializer, PaymentSerializer
from .tasks import calculate_credit_score
from decimal import Decimal, ROUND_HALF_UP
import json
from .utils import LoanProcessor
from datetime import timedelta, datetime
# Create your views here.

class RegisterUserView(APIView):
    def post(self, request):
        
        required_fields = ["name", "email_id", "annual_income", "aadhar_id"]
        
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return Response({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(aadhar_id=request.data.get("aadhar_id")).exists():
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer  = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            calculate_credit_score.delay(user.user_id)
            return Response({"unique_user_id": user.user_id}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


            

class ApplyLoanView(APIView):
    def post(self, request):
        required_fields = ["user_id", "loan_type", "loan_amount", "interest_rate", "term_period", "disbursement_date"]
        
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return Response({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if not User.objects.filter(user_id=request.data.get("user_id")).exists():
            return Response({"error": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(user_id=request.data.get("user_id"))
        
        if user.credit_score < 450:
            return Response({"error": "Credit score is less than 450"}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.annual_income < 150000:
            return Response({"error": "Annual income is less than Rs.1,50,000"}, status=status.HTTP_400_BAD_REQUEST)
        
        if int(request.data.get("loan_amount")) > 5000:
            return Response({"error": "Loan amount is greater than Rs.5000"}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.data.get("loan_type") not in ["credit card"]:
            return Response({"error": "Invalid loan type, only 'credit card' type loan available"}, status=status.HTTP_400_BAD_REQUEST)
        
        if float(request.data.get("interest_rate")) <12:
            return Response({"error": "Interest rate is less than 12%"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        billing_date = datetime.strptime(request.data.get('disbursement_date'), '%Y-%m-%d') + timedelta(days=1)
        processor = LoanProcessor(request.data.get("loan_amount"), request.data.get("interest_rate"), request.data.get("term_period"), billing_date, user)
        response = processor.due_dates
        
        if response == -1:
            return Response({"error": "Interest is less than Rs.50 per month"}, status=status.HTTP_400_BAD_REQUEST)

        if Decimal(processor.emi) > Decimal(user.annual_income/12) * Decimal('0.2'):
            return Response({"error": "EMI is greater than 20% of monthly income"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = LoanSerializer(data=request.data)
        if serializer.is_valid():
            loan = serializer.save(user_id = user)
            due_dates = []
            for i in response:
                
                Billing.objects.create(
                    loan=loan,
                    billing_date= i['due_date'],
                    due_date=i['due_date'] + timedelta(days=15),
                    min_due=i['min_due'],
                    principal_due=i['principal_due'],
                    interest_due=i['interest']
                    
                )
                
                due_dates.append({"date": i['due_date'].strftime("%Y-%m-%d"), "amount_due": float(i['min_due'])})

                
                
            return Response({'loan_id': loan.loan_id, "due_dates": due_dates}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class MakePaymentView(APIView):
    def post(self, request):
        required_fields = ["loan_id", "amount"]
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return Response({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        loan = Loan.objects.filter(loan_id=request.data.get("loan_id")).first()
        if not loan:
            return Response({"error": "Loan not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        billing = Billing.objects.filter(loan_id=loan, due_date__gte=datetime.today().date()).order_by("due_date").first()
        if not billing:
            return Response({"error": "No active billing found for this user"}, status=status.HTTP_400_BAD_REQUEST)
        
        if DuePayment.objects.filter(loan_id=loan, paid=False).exclude(due_date=billing.due_date).exists():
            return Response({"error": "Previous EMIs are unpaid"}, status=status.HTTP_400_BAD_REQUEST)
        
        amount_paid = Decimal(request.data.get("amount"))
        if Payment.objects.filter(loan_id=loan, date=datetime.today().date()).exists():
            return Response({"error": "Payment already recorded for today"}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount_paid != billing.min_due:
            new_emi = (loan.loan_amount - amount_paid) / loan.term_period
            new_emi = new_emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            billing.min_due = new_emi
            billing.save()
            
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(loan_id=loan)
            DuePayment.objects.filter(loan_id=loan, due_date=billing.due_date).update(paid=True)
        
            return Response(status=status.HTTP_200_OK)

class GetStatementView(APIView):
    def get(self, request):
        loan_id = request.query_params.get("loan_id")
        if not loan_id:
            return Response({"error": "Missing required field: loan_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        loan = Loan.objects.filter(loan_id=loan_id).first()
        if not loan:
            return Response({"error": "Loan not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        if loan.term_period == 0:
            return Response({"error": "Loan is closed"}, status=status.HTTP_400_BAD_REQUEST)
        
        past_transactions = Billing.objects.filter(loan_id=loan, due_date__lt=datetime.today().date()).values('due_date', 'principal_due', 'interest_due', 'min_due')
        upcoming_transactions = Billing.objects.filter(loan_id=loan, due_date__gte=datetime.today().date()).values('due_date', 'min_due')
        
        past_transactions_list = [
            {
                "date": transaction["due_date"].strftime("%Y-%m-%d"),
                "principal": float(transaction["principal_due"]),
                "interest": float(transaction["interest_due"]),
                "amount_paid": float(transaction["min_due"])
            }
            for transaction in past_transactions
        ]
        
        upcoming_transactions_list = [
            {
                "date": transaction["due_date"].strftime("%Y-%m-%d"),
                "amount_due": float(transaction["min_due"])
            }
            for transaction in upcoming_transactions
        ]
        
        return Response({
            "error": None,
            "past_transactions": past_transactions_list,
            "upcoming_transactions": upcoming_transactions_list
        }, status=status.HTTP_200_OK)