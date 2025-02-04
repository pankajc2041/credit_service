from django.urls import path
from .views import RegisterUserView, ApplyLoanView, MakePaymentView, GetStatementView

urlpatterns = [
    path("api/register-user/", RegisterUserView.as_view(), name="register_user"),
    path("api/apply-loan/", ApplyLoanView.as_view(), name="apply_loan"),
    path("api/make-payment/", MakePaymentView.as_view(), name="make_payment"),
    path("api/get-statement/", GetStatementView.as_view(), name="get_statement"),
]
