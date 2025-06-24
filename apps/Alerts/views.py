import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import datetime
import logging

from .models import Alert
from apps.portfolios.models import Portfolio

# Set up logging
logger = logging.getLogger(__name__)

class AlertListView(LoginRequiredMixin, generic.ListView):
    """Display a list of all alerts for the current user."""
    model = Alert
    template_name = 'Alerts/index.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        """Return only the user's alerts with related portfolio info."""
        return Alert.objects.filter(user=self.request.user).select_related('portfolio')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_alerts'] = self.get_queryset().filter(status='active').count()
        context['triggered_alerts'] = self.get_queryset().filter(status='triggered').count()
        context['completed_alerts'] = self.get_queryset().filter(status='completed').count()
        
        # Get portfolio alerts count for summary
        context['portfolio_alerts'] = self.get_queryset().exclude(portfolio=None).count()
        
        # Get user's portfolios for the dropdown
        context['portfolios'] = Portfolio.objects.filter(owner=self.request.user)
        
        return context


class AlertCreateView(LoginRequiredMixin, generic.CreateView):
    """Create a new alert."""
    model = Alert
    fields = ['title', 'description', 'symbol', 'condition_type', 'threshold_value', 
              'custom_condition', 'frequency', 'email_notification', 'sound_notification']
    template_name = 'Alerts/alert_form.html'
    success_url = reverse_lazy('Alerts:alert_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Get portfolio_id and stock_id from request if available
        form.instance.portfolio_id = self.request.POST.get('portfolio_id')
        form.instance.stock_id = self.request.POST.get('stock_id')
        
        messages.success(self.request, 'Alert created successfully!')
        return super().form_valid(form)


class AlertUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Update an existing alert."""
    model = Alert
    fields = ['title', 'description', 'symbol', 'condition_type', 'threshold_value', 
              'custom_condition', 'frequency', 'status', 'email_notification', 'sound_notification']
    template_name = 'Alerts/alert_form.html'
    
    def get_queryset(self):
        """Ensure users can only update their own alerts."""
        return Alert.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('Alerts:alert_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Alert updated successfully!')
        return super().form_valid(form)


class AlertDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Delete an alert."""
    model = Alert
    template_name = 'Alerts/alert_confirm_delete.html'
    success_url = reverse_lazy('Alerts:alert_list')
    
    def get_queryset(self):
        """Ensure users can only delete their own alerts."""
        return Alert.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Alert deleted successfully!')
        return super().delete(request, *args, **kwargs)


@method_decorator(csrf_protect, name='dispatch')
class AlertAPIView(LoginRequiredMixin, generic.View):
    """API for CRUD operations on alerts."""
    
    def get(self, request, *args, **kwargs):
        """Get alerts for the current user."""
        try:
            # Get filter parameters
            status = request.GET.get('status')
            alert_id = request.GET.get('id')
            
            # Base query - only user's alerts
            alerts_query = Alert.objects.filter(user=request.user)
            
            # Apply filters if provided
            if status:
                alerts_query = alerts_query.filter(status=status)
            
            if alert_id:
                alerts_query = alerts_query.filter(id=alert_id)
            
            # Convert to list of dictionaries
            alerts_data = []
            for alert in alerts_query:
                alerts_data.append({
                    'id': alert.id,
                    'title': alert.title,
                    'symbol': alert.symbol,
                    'condition_type': alert.condition_type,
                    'condition_display': alert.get_condition_type_display(),
                    'threshold_value': float(alert.threshold_value) if alert.threshold_value else None,
                    'custom_condition': alert.custom_condition,
                    'frequency': alert.frequency,
                    'status': alert.status,
                    'status_display': alert.get_status_display(),
                    'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                    'times_triggered': alert.times_triggered,
                    'email_notification': alert.email_notification,
                    'sound_notification': alert.sound_notification,
                    'created_at': alert.created_at.isoformat(),
                })
            
            return JsonResponse({
                'status': 'success',
                'alerts': alerts_data,
                'count': len(alerts_data)
            })
        
        except Exception as e:
            logger.error(f"Error in AlertAPIView.get: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def post(self, request, *args, **kwargs):
        """Create a new alert."""
        try:
            data = json.loads(request.body)
            
            # Create the alert
            alert = Alert(
                user=request.user,
                title=data.get('title'),
                description=data.get('description'),
                symbol=data.get('symbol'),
                condition_type=data.get('condition_type'),
                threshold_value=data.get('threshold_value'),
                custom_condition=data.get('custom_condition'),
                frequency=data.get('frequency', 'one_time'),
                portfolio_id=data.get('portfolio_id'),
                stock_id=data.get('stock_id'),
                email_notification=data.get('email_notification', True),
                sound_notification=data.get('sound_notification', True)
            )
            alert.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Alert created successfully',
                'alert_id': alert.id
            })
        
        except Exception as e:
            logger.error(f"Error in AlertAPIView.post: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def put(self, request, *args, **kwargs):
        """Update an existing alert."""
        try:
            data = json.loads(request.body)
            alert_id = data.get('id')
            
            if not alert_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Alert ID is required'
                }, status=400)
            
            # Get the alert and verify ownership
            alert = get_object_or_404(Alert, id=alert_id, user=request.user)
            
            # Update fields
            if 'title' in data:
                alert.title = data['title']
            if 'description' in data:
                alert.description = data['description']
            if 'symbol' in data:
                alert.symbol = data['symbol']
            if 'condition_type' in data:
                alert.condition_type = data['condition_type']
            if 'threshold_value' in data:
                alert.threshold_value = data['threshold_value']
            if 'custom_condition' in data:
                alert.custom_condition = data['custom_condition']
            if 'frequency' in data:
                alert.frequency = data['frequency']
            if 'status' in data:
                alert.status = data['status']
            if 'email_notification' in data:
                alert.email_notification = data['email_notification']
            if 'sound_notification' in data:
                alert.sound_notification = data['sound_notification']
            
            alert.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Alert updated successfully'
            })
        
        except Exception as e:
            logger.error(f"Error in AlertAPIView.put: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def delete(self, request, *args, **kwargs):
        """Delete an alert."""
        try:
            data = json.loads(request.body)
            alert_id = data.get('id')
            
            if not alert_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Alert ID is required'
                }, status=400)
            
            # Get the alert and verify ownership
            alert = get_object_or_404(Alert, id=alert_id, user=request.user)
            alert.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Alert deleted successfully'
            })
        
        except Exception as e:
            logger.error(f"Error in AlertAPIView.delete: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


@method_decorator(csrf_protect, name='dispatch')
class AlertNotificationView(LoginRequiredMixin, generic.View):
    """Handle alert notifications like emails and status updates."""
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            alert_id = data.get('alert_id')
            
            if not alert_id:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Alert ID is required'
                }, status=400)
            
            # Get the alert
            alert = get_object_or_404(Alert, id=alert_id, user=request.user)
            
            # Mark as triggered
            alert.mark_as_triggered()
            
            # Send email notification if enabled
            success = True
            message = ''
            
            if alert.email_notification:
                try:
                    self.send_email_notification(request, alert)
                    message = 'Alert triggered and email sent successfully'
                except Exception as e:
                    logger.error(f"Failed to send email notification: {str(e)}")
                    success = False
                    message = f'Alert triggered but failed to send email: {str(e)}'
            else:
                message = 'Alert triggered successfully (email notification disabled)'
            
            return JsonResponse({
                'status': 'success' if success else 'partial',
                'message': message,
                'alert_status': alert.status
            })
        
        except Exception as e:
            logger.error(f"Error in AlertNotificationView.post: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to process notification: {str(e)}'
            }, status=500)
    
    def send_email_notification(self, request, alert):
        """Send an email notification for a triggered alert."""
        recipient_email = request.user.email
        if not recipient_email:
            logger.warning(f"No email address found for user {request.user.id}")
            raise ValueError("User email address not found")
        
        subject = f"Alert Notification: {alert.title}"
        text_message = f"Your alert for {alert.symbol} has been triggered. Condition: {alert.get_condition_type_display()}"
        
        # Context for the email template
        context = {
            'alert': alert,
            'user': request.user,
            'subject': subject,
            'message': text_message,
            'triggered_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'year': datetime.datetime.now().year
        }
        
        # Render HTML message from template string
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #0d6efd; margin: 0;">EK Global Alert Notification</h2>
            </div>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #212529;">{subject}</h3>
                <p style="color: #6c757d;">{text_message}</p>
                <p><strong>Alert Details:</strong></p>
                <ul>
                    <li>Symbol: {alert.symbol}</li>
                    <li>Condition: {alert.get_condition_type_display()}</li>
                    <li>Threshold: {alert.threshold_value if alert.threshold_value else 'N/A'}</li>
                    <li>Triggered: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 20px; font-size: 12px; color: #6c757d; text-align: center;">
                <p>This is an automated notification from your EK Global alerts.</p>
                <p>© {datetime.datetime.now().year} EK Global. All rights reserved.</p>
            </div>
        </div>
        """
        
        try:
            # Create an EmailMultiAlternatives object for better email delivery
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            
            # Attach the HTML version
            email.attach_alternative(html_message, "text/html")
            
            # Send the email
            email.send(fail_silently=False)
            
            logger.info(f"Email notification sent successfully to {recipient_email} for alert {alert.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # Re-raise to handle in the calling function
            raise


@csrf_protect
def create_portfolio_alert(request):
    """Create an alert directly from a portfolio page for a specific stock transaction."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST.dict()
            
            # Required fields
            portfolio_id = data.get('portfolio_id')
            stock_id = data.get('stock_id')
            symbol = data.get('symbol')
            condition_type = data.get('condition_type')
            threshold_value = data.get('threshold_value')
            
            if not all([portfolio_id, symbol, condition_type]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields'
                }, status=400)
            
            # Get the portfolio
            try:
                portfolio = Portfolio.objects.get(id=portfolio_id, owner=request.user)
            except Portfolio.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Portfolio not found'
                }, status=404)
            
            # Create a title if not provided
            title = data.get('title', f"Alert for {symbol} in {portfolio.name}")
            
            # Create the alert
            alert = Alert(
                user=request.user,
                title=title,
                description=data.get('description', f"Portfolio alert for {symbol}"),
                symbol=symbol,
                portfolio=portfolio,
                stock_id=stock_id,
                condition_type=condition_type,
                threshold_value=threshold_value,
                custom_condition=data.get('custom_condition'),
                frequency=data.get('frequency', 'one_time'),
                email_notification=data.get('email_notification', True),
                sound_notification=data.get('sound_notification', True),
            )
            alert.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Alert created successfully',
                    'alert_id': alert.id
                })
            else:
                messages.success(request, 'Alert created successfully!')
                return redirect('portfolios:portfolio_detail', portfolio_id=portfolio_id)
            
        except Exception as e:
            logger.error(f"Error creating portfolio alert: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
            else:
                messages.error(request, f'Error creating alert: {str(e)}')
                return redirect('portfolios:portfolio_detail', portfolio_id=portfolio_id)
    
    # GET requests should redirect to the alerts page
    return redirect('Alerts:alert_list')


# Views
alert_list_view = AlertListView.as_view()
alert_create_view = AlertCreateView.as_view()
alert_update_view = AlertUpdateView.as_view()
alert_delete_view = AlertDeleteView.as_view()
alert_api_view = AlertAPIView.as_view()
alert_notification_view = AlertNotificationView.as_view()
portfolio_alert_create_view = create_portfolio_alert
