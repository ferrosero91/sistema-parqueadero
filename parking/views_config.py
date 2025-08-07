from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import transaction

from .models import Currency, TaxType, TenantConfiguration, Tenant
from .forms_config import CurrencyForm, TaxTypeForm, TenantConfigurationForm, QuickSetupForm
from .decorators import tenant_required, admin_required


# =============================================================================
# VISTAS DE CONFIGURACIÓN GENERAL
# =============================================================================

@login_required
@tenant_required
@admin_required
def configuration_dashboard(request):
    """Dashboard principal de configuraciones"""
    tenant = request.tenant
    
    # Obtener o crear configuración del tenant
    config, created = TenantConfiguration.objects.get_or_create(tenant=tenant)
    
    # Estadísticas
    currencies_count = Currency.objects.filter(tenant=tenant).count()
    tax_types_count = TaxType.objects.filter(tenant=tenant).count()
    
    context = {
        'config': config,
        'currencies_count': currencies_count,
        'tax_types_count': tax_types_count,
        'has_basic_config': config.default_currency is not None,
    }
    
    return render(request, 'parking/config/dashboard.html', context)


@login_required
@tenant_required
@admin_required
def quick_setup(request):
    """Configuración rápida inicial"""
    tenant = request.tenant
    
    if request.method == 'POST':
        form = QuickSetupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear moneda
                    currency_code = form.cleaned_data['currency_choice']
                    currency_data = next(
                        (curr for curr in Currency.get_default_currencies() if curr['code'] == currency_code),
                        None
                    )
                    
                    if currency_data:
                        currency, created = Currency.objects.get_or_create(
                            tenant=tenant,
                            code=currency_data['code'],
                            defaults={
                                'name': currency_data['name'],
                                'symbol': currency_data['symbol'],
                                'decimal_places': currency_data['decimal_places'],
                                'is_active': True,
                                'is_default': True
                            }
                        )
                    
                    # Crear impuesto si se seleccionó
                    tax_type = None
                    tax_choice = form.cleaned_data.get('tax_choice')
                    if tax_choice:
                        tax_code, tax_rate = tax_choice.split('_')
                        tax_data = next(
                            (tax for tax in TaxType.get_default_tax_types() 
                             if tax['code'] == tax_code and str(tax['rate']) == tax_rate),
                            None
                        )
                        
                        if tax_data:
                            tax_type, created = TaxType.objects.get_or_create(
                                tenant=tenant,
                                code=tax_data['code'],
                                rate=tax_data['rate'],
                                defaults={
                                    'name': tax_data['name'],
                                    'description': tax_data['description'],
                                    'is_active': True,
                                    'is_default': True
                                }
                            )
                    
                    # Crear o actualizar configuración
                    config, created = TenantConfiguration.objects.get_or_create(
                        tenant=tenant,
                        defaults={
                            'default_currency': currency,
                            'default_tax_type': tax_type,
                            'apply_tax_by_default': form.cleaned_data.get('apply_tax', False),
                            'include_tax_in_ticket': True,
                            'show_tax_breakdown': True,
                        }
                    )
                    
                    if not created:
                        config.default_currency = currency
                        config.default_tax_type = tax_type
                        config.apply_tax_by_default = form.cleaned_data.get('apply_tax', False)
                        config.save()
                    
                    messages.success(request, 'Configuración inicial completada exitosamente.')
                    return redirect('config-dashboard')
                    
            except Exception as e:
                messages.error(request, f'Error al configurar: {str(e)}')
    else:
        form = QuickSetupForm()
    
    return render(request, 'parking/config/quick_setup.html', {'form': form})


# =============================================================================
# VISTAS DE MONEDAS
# =============================================================================

@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class CurrencyListView(ListView):
    model = Currency
    template_name = 'parking/config/currency_list.html'
    context_object_name = 'currencies'

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.tenant).order_by('name')


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class CurrencyCreateView(CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'parking/config/currency_form.html'
    success_url = reverse_lazy('currency-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        messages.success(self.request, "Moneda creada exitosamente.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class CurrencyUpdateView(UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'parking/config/currency_form.html'
    success_url = reverse_lazy('currency-list')

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Moneda actualizada exitosamente.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class CurrencyDeleteView(DeleteView):
    model = Currency
    template_name = 'parking/config/currency_confirm_delete.html'
    success_url = reverse_lazy('currency-list')

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.tenant)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Moneda eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# VISTAS DE TIPOS DE IMPUESTOS
# =============================================================================

@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class TaxTypeListView(ListView):
    model = TaxType
    template_name = 'parking/config/tax_type_list.html'
    context_object_name = 'tax_types'

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.tenant).order_by('name')


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class TaxTypeCreateView(CreateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'parking/config/tax_type_form.html'
    success_url = reverse_lazy('tax-type-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        messages.success(self.request, "Tipo de impuesto creado exitosamente.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class TaxTypeUpdateView(UpdateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'parking/config/tax_type_form.html'
    success_url = reverse_lazy('tax-type-list')

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Tipo de impuesto actualizado exitosamente.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(tenant_required, name='dispatch')
@method_decorator(admin_required, name='dispatch')
class TaxTypeDeleteView(DeleteView):
    model = TaxType
    template_name = 'parking/config/tax_type_confirm_delete.html'
    success_url = reverse_lazy('tax-type-list')

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.tenant)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Tipo de impuesto eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# VISTAS DE CONFIGURACIÓN DEL TENANT
# =============================================================================

@login_required
@tenant_required
@admin_required
def tenant_configuration(request):
    """Configuración general del tenant"""
    tenant = request.tenant
    config, created = TenantConfiguration.objects.get_or_create(tenant=tenant)
    
    if request.method == 'POST':
        form = TenantConfigurationForm(request.POST, request.FILES, instance=config, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración actualizada exitosamente.")
            return redirect('tenant-configuration')
    else:
        form = TenantConfigurationForm(instance=config, tenant=tenant)
    
    return render(request, 'parking/config/tenant_configuration.html', {
        'form': form,
        'config': config
    })


# =============================================================================
# VISTAS AJAX
# =============================================================================

@login_required
@tenant_required
def toggle_currency_status(request, pk):
    """Activar/desactivar moneda via AJAX"""
    if request.method == 'POST':
        try:
            currency = get_object_or_404(Currency, pk=pk, tenant=request.tenant)
            currency.is_active = not currency.is_active
            currency.save()
            
            return JsonResponse({
                'success': True,
                'is_active': currency.is_active,
                'message': f'Moneda {"activada" if currency.is_active else "desactivada"} exitosamente.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@tenant_required
def toggle_tax_type_status(request, pk):
    """Activar/desactivar tipo de impuesto via AJAX"""
    if request.method == 'POST':
        try:
            tax_type = get_object_or_404(TaxType, pk=pk, tenant=request.tenant)
            tax_type.is_active = not tax_type.is_active
            tax_type.save()
            
            return JsonResponse({
                'success': True,
                'is_active': tax_type.is_active,
                'message': f'Tipo de impuesto {"activado" if tax_type.is_active else "desactivado"} exitosamente.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@tenant_required
def set_default_currency(request, pk):
    """Establecer moneda por defecto via AJAX"""
    if request.method == 'POST':
        try:
            currency = get_object_or_404(Currency, pk=pk, tenant=request.tenant)
            
            # Desmarcar todas las monedas como default
            Currency.objects.filter(tenant=request.tenant).update(is_default=False)
            
            # Marcar esta como default
            currency.is_default = True
            currency.save()
            
            # Actualizar configuración del tenant
            config, created = TenantConfiguration.objects.get_or_create(tenant=request.tenant)
            config.default_currency = currency
            config.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{currency.name} establecida como moneda por defecto.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@tenant_required
def set_default_tax_type(request, pk):
    """Establecer tipo de impuesto por defecto via AJAX"""
    if request.method == 'POST':
        try:
            tax_type = get_object_or_404(TaxType, pk=pk, tenant=request.tenant)
            
            # Desmarcar todos los impuestos como default
            TaxType.objects.filter(tenant=request.tenant).update(is_default=False)
            
            # Marcar este como default
            tax_type.is_default = True
            tax_type.save()
            
            # Actualizar configuración del tenant
            config, created = TenantConfiguration.objects.get_or_create(tenant=request.tenant)
            config.default_tax_type = tax_type
            config.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{tax_type.name} establecido como impuesto por defecto.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


# =============================================================================
# ALIAS PARA MANTENER COMPATIBILIDAD
# =============================================================================

# Alias para el dashboard principal
config_dashboard = configuration_dashboard