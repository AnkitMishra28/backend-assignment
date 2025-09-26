
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer
from django.shortcuts import get_object_or_404
from datetime import date
import math

class RegisterView(APIView):
	def post(self, request):
		data = request.data
		monthly_income = int(data.get('monthly_income'))
		approved_limit = round(36 * monthly_income / 100000) * 100000
		customer = Customer.objects.create(
			first_name=data.get('first_name'),
			last_name=data.get('last_name'),
			age=data.get('age'),
			monthly_salary=monthly_income,
			approved_limit=approved_limit,
			phone_number=data.get('phone_number'),
		)
		serializer = CustomerSerializer(customer)
		return Response(serializer.data, status=status.HTTP_201_CREATED)

class CheckEligibilityView(APIView):
	def post(self, request):
		data = request.data
		customer_id = data.get('customer_id')
		loan_amount = float(data.get('loan_amount'))
		interest_rate = float(data.get('interest_rate'))
		tenure = int(data.get('tenure'))
		customer = get_object_or_404(Customer, customer_id=customer_id)
		loans = Loan.objects.filter(customer=customer)
		# Credit score calculation
		credit_score = 100
		total_current_loans = sum(l.loan_amount for l in loans if l.is_approved)
		if total_current_loans > customer.approved_limit:
			credit_score = 0
		else:
			paid_on_time = sum(l.emis_paid_on_time for l in loans)
			num_loans = loans.count()
			current_year = date.today().year
			current_year_loans = loans.filter(start_date__year=current_year).count()
			approved_volume = sum(l.loan_amount for l in loans if l.is_approved)
			# Weighted scoring (example)
			credit_score = (
				(paid_on_time / (num_loans or 1)) * 30 +
				num_loans * 10 +
				current_year_loans * 10 +
				(approved_volume / (customer.approved_limit or 1)) * 50
			)
		# EMI check
		total_emis = sum(l.monthly_repayment for l in loans if l.is_approved)
		if total_emis > 0.5 * customer.monthly_salary:
			return Response({
				'customer_id': customer_id,
				'approval': False,
				'interest_rate': interest_rate,
				'corrected_interest_rate': None,
				'tenure': tenure,
				'monthly_installment': None
			}, status=status.HTTP_200_OK)
		# Interest rate correction
		corrected_interest_rate = interest_rate
		if credit_score > 50:
			approval = True
			corrected_interest_rate = interest_rate
		elif 50 > credit_score > 30:
			approval = True
			if interest_rate <= 12:
				corrected_interest_rate = 12
		elif 30 >= credit_score > 10:
			approval = True
			if interest_rate <= 16:
				corrected_interest_rate = 16
		else:
			approval = False
			corrected_interest_rate = None
		# Compound interest monthly installment calculation
		if approval:
			r = corrected_interest_rate / 1200
			emi = loan_amount * r * math.pow(1 + r, tenure) / (math.pow(1 + r, tenure) - 1)
		else:
			emi = None
		return Response({
			'customer_id': customer_id,
			'approval': approval,
			'interest_rate': interest_rate,
			'corrected_interest_rate': corrected_interest_rate,
			'tenure': tenure,
			'monthly_installment': emi
		}, status=status.HTTP_200_OK)

class CreateLoanView(APIView):
	def post(self, request):
		data = request.data
		customer_id = data.get('customer_id')
		loan_amount = float(data.get('loan_amount'))
		interest_rate = float(data.get('interest_rate'))
		tenure = int(data.get('tenure'))
		customer = get_object_or_404(Customer, customer_id=customer_id)
		# Check eligibility
		# Reuse CheckEligibilityView logic
		loans = Loan.objects.filter(customer=customer)
		credit_score = 100
		total_current_loans = sum(l.loan_amount for l in loans if l.is_approved)
		if total_current_loans > customer.approved_limit:
			credit_score = 0
		else:
			paid_on_time = sum(l.emis_paid_on_time for l in loans)
			num_loans = loans.count()
			current_year = date.today().year
			current_year_loans = loans.filter(start_date__year=current_year).count()
			approved_volume = sum(l.loan_amount for l in loans if l.is_approved)
			credit_score = (
				(paid_on_time / (num_loans or 1)) * 30 +
				num_loans * 10 +
				current_year_loans * 10 +
				(approved_volume / (customer.approved_limit or 1)) * 50
			)
		total_emis = sum(l.monthly_repayment for l in loans if l.is_approved)
		if total_emis > 0.5 * customer.monthly_salary:
			return Response({
				'loan_id': None,
				'customer_id': customer_id,
				'loan_approved': False,
				'message': 'EMI exceeds 50% of monthly salary',
				'monthly_installment': None
			}, status=status.HTTP_200_OK)
		corrected_interest_rate = interest_rate
		if credit_score > 50:
			approval = True
			corrected_interest_rate = interest_rate
		elif 50 > credit_score > 30:
			approval = True
			if interest_rate <= 12:
				corrected_interest_rate = 12
		elif 30 >= credit_score > 10:
			approval = True
			if interest_rate <= 16:
				corrected_interest_rate = 16
		else:
			approval = False
			corrected_interest_rate = None
		if approval:
			r = corrected_interest_rate / 1200
			emi = loan_amount * r * math.pow(1 + r, tenure) / (math.pow(1 + r, tenure) - 1)
			loan = Loan.objects.create(
				customer=customer,
				loan_amount=loan_amount,
				tenure=tenure,
				interest_rate=corrected_interest_rate,
				monthly_repayment=emi,
				emis_paid_on_time=0,
				start_date=date.today(),
				end_date=date.today().replace(year=date.today().year + tenure // 12),
				is_approved=True,
			)
			return Response({
				'loan_id': loan.loan_id,
				'customer_id': customer_id,
				'loan_approved': True,
				'message': 'Loan approved',
				'monthly_installment': emi
			}, status=status.HTTP_201_CREATED)
		else:
			return Response({
				'loan_id': None,
				'customer_id': customer_id,
				'loan_approved': False,
				'message': 'Loan not approved',
				'monthly_installment': None
			}, status=status.HTTP_200_OK)

class ViewLoanView(APIView):
	def get(self, request, loan_id):
		loan = get_object_or_404(Loan, loan_id=loan_id)
		customer = loan.customer
		return Response({
			'loan_id': loan.loan_id,
			'customer': {
				'id': customer.customer_id,
				'first_name': customer.first_name,
				'last_name': customer.last_name,
				'phone_number': customer.phone_number,
				'age': customer.age,
			},
			'loan_amount': loan.loan_amount,
			'interest_rate': loan.interest_rate,
			'monthly_installment': loan.monthly_repayment,
			'tenure': loan.tenure,
			'is_approved': loan.is_approved,
		}, status=status.HTTP_200_OK)

class ViewLoansByCustomerView(APIView):
	def get(self, request, customer_id):
		customer = get_object_or_404(Customer, customer_id=customer_id)
		loans = Loan.objects.filter(customer=customer, is_approved=True)
		result = []
		for loan in loans:
			repayments_left = loan.tenure - loan.emis_paid_on_time
			result.append({
				'loan_id': loan.loan_id,
				'loan_amount': loan.loan_amount,
				'interest_rate': loan.interest_rate,
				'monthly_installment': loan.monthly_repayment,
				'repayments_left': repayments_left,
				'is_approved': loan.is_approved,
			})
		return Response(result, status=status.HTTP_200_OK)
