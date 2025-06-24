from typing import Any, Dict
import json
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from .models import Portfolio, Investment
from apps.stocks.models import Stock
from .forms import PortfolioCreateForm, InvestmentAddForm, PortfolioUpdateForm
from helpers.exceptions import capture
from helpers.logging import log_exception
from .helpers import (
    get_investments_allocation_piechart_data,
    get_portfolio_performance_graph_data,
    get_stocks_invested_from_investments,
)
from .transactions_upload import (
    handle_transactions_file,
    get_transactions_upload_template,
    TransactionUploadError,
    EXPECTED_TRANSACTION_COLUMNS,
)
from .stock_summary import generate_portfolio_stocks_summary


portfolio_qs = Portfolio.objects.select_related("owner").all()


import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import QuerySet
from typing import Any, Dict

logger = logging.getLogger(__name__)

class PortfolioListView(LoginRequiredMixin, generic.ListView):
    context_object_name = "portfolios"
    paginate_by = 30
    queryset = portfolio_qs
    template_name = "portfolios/portfolio_list.html"
    http_method_names = ["get", "post"]

    def get_queryset(self) -> QuerySet[Portfolio]:
        user = self.request.user
        qs = super().get_queryset()
        return qs.filter(owner=user)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all investments for the user's portfolios
        investments = Investment.objects.filter(
            portfolio__owner=user
        ).select_related('stock', 'portfolio')
        
        # Group investments by stock and portfolio
        holdings_data = []
        for investment in investments:
            stock = investment.stock
            portfolio = investment.portfolio
            
            # Calculate return percentage
            try:
                if stock and stock.price and investment.rate:
                    return_percentage = ((stock.price - investment.rate) / investment.rate) * 100
                else:
                    return_percentage = 0
            except (TypeError, ZeroDivisionError):
                return_percentage = 0
            
            holdings_data.append({
                'client_id': f'CL-{portfolio.id.hex[:4]}',
                'symbol': stock.ticker if stock else 'N/A',
                'company_name': stock.title if stock else 'N/A',
                'quantity': investment.quantity,
                'avg_cost': investment.rate,
                'market_price': stock.price if stock else investment.rate,
                'return_percentage': return_percentage,
                'portfolio_id': str(portfolio.id),
                'stock_id': str(stock.id) if stock else None
            })
        
        context['holdings_data'] = holdings_data
        return context

    def post(self, request, *args, **kwargs):
         """Handle transaction file uploads with detailed debugging"""
         import logging
         logger = logging.getLogger(__name__)
            
         logger.info("=== POST method called ===")
         logger.info(f"User: {request.user}")
         logger.info(f"FILES: {request.FILES}")
            
         transactions_file = request.FILES.get("transactions_file", None)
            
         if not transactions_file:
                logger.error("No file uploaded")
                messages.error(request, "No file was uploaded.")
                return redirect("portfolios:portfolio_list")
            
         logger.info(f"File received: {transactions_file.name}, Size: {transactions_file.size}")
            
         try:
                logger.info(f"Starting transaction upload for user: {request.user}")
                
                # Check initial investment count
                initial_count = Investment.objects.filter(portfolio__owner=request.user).count()
                logger.info(f"Initial investment count for user: {initial_count}")
                
                # The handle_transactions_file function returns None, not a dict
                handle_transactions_file(transactions_file, request.user)
                
                # Check final investment count
                final_count = Investment.objects.filter(portfolio__owner=request.user).count()
                logger.info(f"Final investment count for user: {final_count}")
                logger.info(f"New investments created: {final_count - initial_count}")
                
                logger.info("Transaction upload completed successfully")
                messages.success(request, f"Transactions uploaded successfully! Created {final_count - initial_count} investments.")
                return redirect("portfolios:portfolio_list")
                
         except TransactionUploadError as exc:
                logger.error(f"TransactionUploadError: {exc}")
                messages.error(request, str(exc))
         except Exception as exc:
                logger.error(f"Unexpected error during transaction upload: {exc}")
                logger.error(f"Exception type: {type(exc).__name__}")
                logger.error(f"Exception details: {exc}", exc_info=True)
                messages.error(
                    request,
                    f"Upload failed! Error: {str(exc)}. Ensure the file is in the correct format and contains the required data.",
                )

         return redirect("portfolios:portfolio_list")
    
class TransactionsUploadTemplateDownloadView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        template = get_transactions_upload_template()

        if not template:
            return HttpResponse(status=404)
        headers = {
            "Content-Disposition": f"attachment; filename={template.name}",
            "Content-Type": template.content_type,
        }
        return HttpResponse(content=template, headers=headers, status=200)


@capture.enable
class PortfolioCreateView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]
    form_class = PortfolioCreateForm

    @capture.capture(content="Oops! An error occurred")
    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        form = self.form_class(data={"owner": request.user, **data})

        if not form.is_valid():
            return JsonResponse(
                data={
                    "status": "error",
                    "detail": "An error occurred",
                    "errors": form.errors,
                },
                status=400,
            )
        form.save()
        return JsonResponse(
            data={
                "status": "success",
                "detail": "Portfolio created successfully",
                "redirect_url": reverse("portfolios:portfolio_list"),
            },
            status=200,
        )


# Use list view for detail view so Investments can be paginated.
# Instead, add the portfolio to the context
class PortfolioDetailView(LoginRequiredMixin, generic.ListView):
    template_name = "portfolios/portfolio_detail.html"
    queryset = Investment.objects.all()
    paginate_by = 100
    context_object_name = "investments"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        investments = context["investments"]
        portfolio = get_object_or_404(
            portfolio_qs.prefetch_related(
                "investments"
            ),
            id=self.kwargs["portfolio_id"],
            owner=self.request.user,
        )
        stocks_summary_dt_filter = self.request.GET.get("filter_summary_by", "5D")

        context["portfolio"] = portfolio
        context["all_stocks"] = Stock.objects.values("ticker", "title")
        context["invested_stocks"] = get_stocks_invested_from_investments(
            investments.select_related("stock")
        )
        context["pie_chart_data"] = json.dumps(
            get_investments_allocation_piechart_data(
                investments.select_related("stock")
            )
        )

        # Performance data is no longer calculated and sent pre-page load
        # as it is it very costly and increases page load time (even with query optimizations)
        # Hence, client should fetch performance data via the `PortfolioPerformanceDataView` after the page loads
        # context["line_chart_data"] = json.dumps(
        #     get_portfolio_performance_graph_data(portfolio)
        # )
        context["stocks_summary"] = generate_portfolio_stocks_summary(
            portfolio,
            dt_filter=stocks_summary_dt_filter,
            timezone=str(self.request.user.timezone),
        )
        context["stocks_summary_dt_filter"] = stocks_summary_dt_filter
        return context

    def get_queryset(self) -> QuerySet[Portfolio]:
        user = self.request.user
        qs = super().get_queryset()
        return (
            qs.filter(portfolio_id=self.kwargs["portfolio_id"], portfolio__owner=user)
            .select_related("stock")
            # .prefetch_related("stock__rates")
        )


@capture.enable
@capture.capture(content="Oops! An error occurred")
class PortfolioPerformanceDataView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]

    def get_object(self):
        # Note that the portfolio queryset is used not the model.
        # This is because the queryset has prefetched and selected related data
        # Making it way more efficient that using the model
        return get_object_or_404(
            portfolio_qs.prefetch_related("investments", "investments__stock"),
            id=self.kwargs["portfolio_id"],
        )

    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        dt_filter = data.get("dt_filter", "5D")
        stocks = data.get("stocks", None)
        timezone = data.get("timezone", str(request.user.timezone))
        portfolio = self.get_object()
        data = get_portfolio_performance_graph_data(
            portfolio=portfolio,
            dt_filter=dt_filter,
            stocks=stocks,
            timezone=timezone,
        )
        return JsonResponse(
            data={
                "status": "success",
                "detail": "Performance data fetched successfully",
                "data": data,
            },
            status=200,
        )


@capture.enable
@capture.capture(content="Oops! An error occurred")
class PortfolioUpdateView(LoginRequiredMixin, generic.View):
    http_method_names = ["patch"]
    form_class = PortfolioUpdateForm

    def get_object(self):
        return get_object_or_404(portfolio_qs, id=self.kwargs["portfolio_id"])

    def patch(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        form = self.form_class(data=data, instance=self.get_object())

        if not form.is_valid():
            return JsonResponse(
                data={
                    "status": "error",
                    "detail": "An error occurred",
                    "errors": form.errors,
                },
                status=400,
            )
        form.save()
        return JsonResponse(
            data={
                "status": "success",
                "detail": "Portfolio updated successfully",
                "redirect_url": reverse("portfolios:portfolio_list"),
            },
            status=200,
        )


class PortfolioDeleteView(LoginRequiredMixin, generic.View):
    queryset = portfolio_qs
    http_method_names = ["get"]

    def get_queryset(self) -> QuerySet[Portfolio]:
        user = self.request.user
        qs = self.queryset
        return qs.filter(owner=user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), id=self.kwargs["portfolio_id"])

    def get(self, request, *args, **kwargs):
        portfolio = self.get_object()
        portfolio.delete()
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("portfolios:portfolio_list")


@capture.enable
class PortfolioDividendsUpdateView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]
    form_class = PortfolioUpdateForm

    def get_object(self):
        return get_object_or_404(
            portfolio_qs, id=self.kwargs["portfolio_id"], owner=self.request.user
        )

    @capture.capture(content="Oops! An error occurred")
    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        portfolio = self.get_object()
        form = self.form_class(
            data={"dividends": data["dividends"], "name": portfolio.name},
            instance=portfolio,
        )

        if not form.is_valid():
            return JsonResponse(
                data={
                    "status": "error",
                    "detail": "An error occurred",
                    "errors": form.errors,
                },
                status=400,
            )
        form.save()
        return JsonResponse(
            data={
                "status": "success",
                "detail": "Dividend receipt was recorded successfully",
                "redirect_url": reverse(
                    "portfolios:portfolio_detail", kwargs={"portfolio_id": portfolio.id}
                ),
            },
            status=200,
        )


@capture.enable
class InvestmentAddView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]
    form_class = InvestmentAddForm

    @capture.capture(content="Oops! An error occurred")
    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        portfolio_id = self.kwargs["portfolio_id"]
        data.update(
            {
                "portfolio": portfolio_id,
            }
        )
        form = self.form_class(data)

        if not form.is_valid():
            return JsonResponse(
                data={
                    "status": "error",
                    "detail": "An error occurred",
                    "errors": form.errors,
                },
                status=400,
            )
        form.save()
        return JsonResponse(
            data={
                "status": "success",
                "detail": "Investment added successfully",
                "redirect_url": reverse(
                    "portfolios:portfolio_detail", kwargs={"portfolio_id": portfolio_id}
                ),
            },
            status=200,
        )


class InvestmentDeleteView(LoginRequiredMixin, generic.View):
    queryset = Investment.objects.select_related("portfolio", "portfolio__owner")
    http_method_names = ["get"]

    def get_queryset(self) -> QuerySet[Investment]:
        user = self.request.user
        portfolio_id = self.kwargs["portfolio_id"]
        qs = self.queryset
        return qs.filter(portfolio_id=portfolio_id, portfolio__owner=user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), id=self.kwargs["investment_id"])

    def get(self, request, *args, **kwargs):
        investment = self.get_object()
        investment.delete()
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "portfolios:portfolio_detail",
            kwargs={"portfolio_id": self.kwargs["portfolio_id"]},
        )


class TransactionCompareView(LoginRequiredMixin, generic.TemplateView):
    """View for comparing transactions from different dates."""
    template_name = "portfolios/transaction_compare.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all portfolios for the user
        portfolios = Portfolio.objects.filter(owner=user)
        
        # Get selected portfolio(s)
        portfolio_id = self.request.GET.get('portfolio_id')
        selected_portfolio = None
        
        if portfolio_id:
            try:
                selected_portfolio = portfolios.get(id=portfolio_id)
            except Portfolio.DoesNotExist:
                selected_portfolio = None
        
        # Get all unique transaction dates for the user's investments
        investments_query = Investment.objects.filter(portfolio__owner=user)
        
        # Filter by portfolio if selected
        if selected_portfolio:
            investments_query = investments_query.filter(portfolio=selected_portfolio)
            
        investments = investments_query.annotate(
            transaction_day=TruncDate('transaction_date')
        ).values('transaction_day').distinct().order_by('-transaction_day')
        
        # Get the dates as a list
        transaction_dates = [inv['transaction_day'] for inv in investments if inv['transaction_day']]
        
        # Default to the two most recent dates if available
        date1 = self.request.GET.get('date1')
        date2 = self.request.GET.get('date2')
        
        if date1:
            try:
                date1 = datetime.datetime.strptime(date1, '%Y-%m-%d').date()
            except ValueError:
                date1 = None
        
        if date2:
            try:
                date2 = datetime.datetime.strptime(date2, '%Y-%m-%d').date()
            except ValueError:
                date2 = None
        
        # If dates are not provided or invalid, use the two most recent dates
        if not date1 and len(transaction_dates) > 0:
            date1 = transaction_dates[0]
        
        if not date2 and len(transaction_dates) > 1:
            date2 = transaction_dates[1]
        
        # Get transactions for the selected dates
        transactions1 = []
        transactions2 = []
        
        transactions_query = Investment.objects.filter(portfolio__owner=user)
        
        # Filter by portfolio if selected
        if selected_portfolio:
            transactions_query = transactions_query.filter(portfolio=selected_portfolio)
        
        # Get selected stocks to compare
        selected_stocks = self.request.GET.getlist('stocks')
        
        if date1:
            date1_query = transactions_query.filter(transaction_date=date1)
            if selected_stocks:
                date1_query = date1_query.filter(stock__ticker__in=selected_stocks)
            transactions1 = date1_query.select_related('stock', 'portfolio')
        
        if date2:
            date2_query = transactions_query.filter(transaction_date=date2)
            if selected_stocks:
                date2_query = date2_query.filter(stock__ticker__in=selected_stocks)
            transactions2 = date2_query.select_related('stock', 'portfolio')
        
        # Get all available stocks for selection
        all_available_stocks = set()
        for t in Investment.objects.filter(portfolio__owner=user).select_related('stock'):
            if t.stock:
                all_available_stocks.add((t.stock.ticker, t.stock.title))
        
        # Prepare comparison data
        comparison_data = []
        
        # Create a set of all symbols from both transaction sets
        all_symbols = set()
        for t in transactions1:
            if t.stock:
                all_symbols.add(t.stock.ticker)
        
        for t in transactions2:
            if t.stock:
                all_symbols.add(t.stock.ticker)
        
        # For each symbol, find the transactions and compare them
        for symbol in all_symbols:
            t1_list = [t for t in transactions1 if t.stock and t.stock.ticker == symbol]
            t2_list = [t for t in transactions2 if t.stock and t.stock.ticker == symbol]
            
            # Calculate totals for date1
            t1_buy_qty = sum(t.quantity for t in t1_list if t.transaction_type == 'buy')
            t1_sell_qty = sum(t.quantity for t in t1_list if t.transaction_type == 'sell')
            t1_avg_rate = sum(t.rate * t.quantity for t in t1_list) / sum(t.quantity for t in t1_list) if t1_list else 0
            t1_total_cost = sum(t.cost for t in t1_list)
            
            # Calculate totals for date2
            t2_buy_qty = sum(t.quantity for t in t2_list if t.transaction_type == 'buy')
            t2_sell_qty = sum(t.quantity for t in t2_list if t.transaction_type == 'sell')
            t2_avg_rate = sum(t.rate * t.quantity for t in t2_list) / sum(t.quantity for t in t2_list) if t2_list else 0
            t2_total_cost = sum(t.cost for t in t2_list)
            
            # Calculate differences
            qty_diff = (t1_buy_qty - t1_sell_qty) - (t2_buy_qty - t2_sell_qty)
            rate_diff = t1_avg_rate - t2_avg_rate
            cost_diff = t1_total_cost - t2_total_cost
            
            # Get stock name
            stock_name = t1_list[0].stock.title if t1_list else (t2_list[0].stock.title if t2_list else "Unknown")
            
            comparison_data.append({
                'ticker': symbol,
                'name': stock_name,
                'date1': {
                    'buy_qty': t1_buy_qty,
                    'sell_qty': t1_sell_qty,
                    'net_qty': t1_buy_qty - t1_sell_qty,
                    'avg_rate': t1_avg_rate,
                    'total_cost': t1_total_cost
                },
                'date2': {
                    'buy_qty': t2_buy_qty,
                    'sell_qty': t2_sell_qty,
                    'net_qty': t2_buy_qty - t2_sell_qty,
                    'avg_rate': t2_avg_rate,
                    'total_cost': t2_total_cost
                },
                'diff': {
                    'qty': qty_diff,
                    'rate': rate_diff,
                    'cost': cost_diff
                }
            })
        
        # Sort comparison data by symbol
        comparison_data.sort(key=lambda x: x['ticker'])
        
        context.update({
            'portfolios': portfolios,
            'selected_portfolio': selected_portfolio,
            'transaction_dates': transaction_dates,
            'date1': date1,
            'date2': date2,
            'comparison_data': comparison_data,
            'all_available_stocks': sorted(all_available_stocks),
            'selected_stocks': selected_stocks
        })
        
        return context


@method_decorator(csrf_protect, name='dispatch')
class EmailNotificationView(LoginRequiredMixin, generic.View):
    """API endpoint for sending email notifications."""
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            recipient_email = data.get('recipient_email')
            subject = data.get('subject', 'Alert Notification')
            message = data.get('message', 'You have a new alert from EK Global.')
            send_now = data.get('send_now', True)
            
            if not recipient_email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Recipient email is required'
                }, status=400)
            
            # Validate email is associated with the user's account
            if recipient_email != request.user.email and not request.user.is_staff:
                # Option: Only allow sending to verified emails
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email notifications can only be sent to your account email'
                }, status=403)
            
            # Format the email with a professional template
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 5px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #0d6efd; margin: 0;">EK Global Alert Notification</h2>
                </div>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #212529;">{subject}</h3>
                    <p style="color: #6c757d;">{message}</p>
                </div>
                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 20px; font-size: 12px; color: #6c757d; text-align: center;">
                    <p>This is an automated notification from your EK Global portfolio alerts.</p>
                    <p>© {datetime.datetime.now().year} EK Global. All rights reserved.</p>
                </div>
            </div>
            """
            
            if send_now:
                # Send the email
                send_mail(
                    subject=subject,
                    message=message,  # Plain text version
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    html_message=html_message,  # HTML version
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Email notification sent to {recipient_email}'
                })
            else:
                # Queue the email for later sending (you'd use Celery or similar here)
                # For now, we'll just send it immediately
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Email notification queued for {recipient_email}'
                })
                
        except Exception as e:
            log_exception(e)
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send email notification: {str(e)}'
            }, status=500)


def image_test_view(request):
    """View to test if static images load correctly."""
    return render(request, "portfolios/image-test.html")


@method_decorator(csrf_protect, name='dispatch')
class PortfolioTransactionsAPIView(LoginRequiredMixin, generic.View):
    """API endpoint to fetch portfolio transactions from the database."""
    http_method_names = ['get']
    
    def _get_stock_data(self, stock, transaction_rate):
        """
        Helper function to safely get stock data with proper error handling and fallbacks
        
        Args:
            stock: The stock model instance
            transaction_rate: The transaction rate to use as fallback
            
        Returns:
            tuple: (current_price, avg_buy_rate)
        """
        # Initialize with safe defaults
        current_price = None
        avg_buy_rate = 0
        
        # Handle potential attribute errors safely
        try:
            # Try to get current price from different possible attributes
            if hasattr(stock, 'price') and stock.price is not None:
                current_price = stock.price
            elif hasattr(stock, 'current_rate') and stock.current_rate is not None:
                current_price = stock.current_rate
                
            # Try to get average buy rate if it exists
            if hasattr(stock, 'avg_buy_rate') and stock.avg_buy_rate is not None:
                avg_buy_rate = stock.avg_buy_rate
        except Exception as e:
            # Log the error but continue with defaults
            log_exception(e)
            
        # Use transaction rate as fallback if current_price is still None
        if current_price is None:
            current_price = transaction_rate
            
        return current_price, avg_buy_rate
    
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            portfolio_id = request.GET.get('portfolio_id')
            limit = int(request.GET.get('limit', 50))
            
            # Query for investments (transactions)
            query = Investment.objects.filter(portfolio__owner=user)
            
            # Filter by portfolio if specified
            if portfolio_id:
                query = query.filter(portfolio_id=portfolio_id)
            
            # Get the latest transactions
            transactions = query.select_related('stock', 'portfolio').order_by('-transaction_date')[:limit]
            
            # Format transactions for frontend
            transaction_data = []
            for transaction in transactions:
                # Get stock data safely
                current_price, avg_buy_rate = self._get_stock_data(transaction.stock, transaction.rate)
                
                # Calculate return
                try:
                    if transaction.transaction_type.lower() == 'buy':
                        return_value = ((current_price - transaction.rate) / transaction.rate) * 100
                    else:  # For sell transactions
                        return_value = ((transaction.rate - avg_buy_rate) / avg_buy_rate) * 100 if avg_buy_rate else 0
                except (TypeError, ZeroDivisionError):
                    # Handle calculation errors
                    return_value = 0
                
                # Create the transaction object
                try:
                    transaction_data.append({
                        'id': str(transaction.id),
                        'clientId': f'CL-{transaction.portfolio.id.hex[:4]}',
                        'symbol': transaction.stock.ticker,
                        'name': transaction.stock.title,
                        'quantity': float(transaction.quantity),
                        'avgCost': float(transaction.rate),
                        'marketPrice': float(current_price),
                        'return': round(return_value, 2),
                        'transactionType': transaction.transaction_type,
                        'transactionDate': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                        'portfolio': {
                            'id': str(transaction.portfolio.id),
                            'name': transaction.portfolio.name
                        }
                    })
                except Exception as e:
                    # Log specific errors in data formatting but continue with other transactions
                    log_exception(e)
                    continue
            
            return JsonResponse({
                'status': 'success',
                'transactions': transaction_data,
                'count': len(transaction_data),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            log_exception(e)
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to fetch transactions: {str(e)}'
            }, status=500)


class PortfolioNewsAPIView(LoginRequiredMixin, generic.View):
    """API endpoint to fetch financial news for stocks in a portfolio."""
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        from apps.dashboard.api_client import MarketDataAPIClient
        
        try:
            # Get portfolio ID if provided
            portfolio_id = request.GET.get('portfolio_id', None)
            
            # Initialize the API client
            api_client = MarketDataAPIClient()
            
            # Fetch general news if no portfolio is specified
            if not portfolio_id:
                news = api_client.get_news(limit=10)
                return JsonResponse({
                    'status': 'success',
                    'news': news
                })
            
            # Get portfolio and related stock symbols
            portfolio = get_object_or_404(Portfolio, id=portfolio_id, owner=request.user)
            investments = Investment.objects.filter(portfolio=portfolio).select_related('stock')
            
            # Extract stock symbols from investments
            stock_symbols = [investment.stock.ticker for investment in investments if investment.stock]
            
            if not stock_symbols:
                # If no stocks in portfolio, return general news
                news = api_client.get_news(limit=10)
            else:
                # Fetch news related to the portfolio's stocks
                # Note: This assumes the API client has the capability to filter by stock symbols
                # If not, we would need to fetch all news and filter here
                news = api_client.get_news(limit=20)
                
                # Filter news by stock symbols (if API doesn't support filtering)
                filtered_news = []
                for news_item in news:
                    # Check if any portfolio stock is mentioned in the news
                    if any(symbol in news_item.get('Tags', '') or 
                           symbol in news_item.get('Headline', '') or 
                           symbol in news_item.get('Description', '') 
                           for symbol in stock_symbols):
                        filtered_news.append(news_item)
                
                # Use filtered news if available, otherwise use general news
                if filtered_news:
                    news = filtered_news[:10]  # Limit to 10 relevant news items
            
            return JsonResponse({
                'status': 'success',
                'portfolio_id': str(portfolio_id) if portfolio_id else None,
                'news': news
            })
            
        except Exception as e:
            log_exception(e)
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


portfolio_list_view = PortfolioListView.as_view()
transactions_upload_template_download_view = (
    TransactionsUploadTemplateDownloadView.as_view()
)
portfolio_create_view = PortfolioCreateView.as_view()
portfolio_detail_view = PortfolioDetailView.as_view()
portfolio_performance_data_view = PortfolioPerformanceDataView.as_view()
portfolio_update_view = PortfolioUpdateView.as_view()
portfolio_delete_view = PortfolioDeleteView.as_view()
portfolio_dividends_update_view = PortfolioDividendsUpdateView.as_view()
investment_add_view = InvestmentAddView.as_view()
investment_delete_view = InvestmentDeleteView.as_view()
transaction_compare_view = TransactionCompareView.as_view()
email_notification_view = EmailNotificationView.as_view()
portfolio_transactions_api_view = PortfolioTransactionsAPIView.as_view()
portfolio_news_api_view = PortfolioNewsAPIView.as_view()
