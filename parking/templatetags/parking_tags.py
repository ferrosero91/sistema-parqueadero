"""
Template tags personalizados para el sistema de parqueadero
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_currency(amount, tenant=None):
    """
    Formatear un monto según la configuración del tenant
    Uso: {{ amount|format_currency:request.tenant }}
    """
    if not amount:
        return "0"
    
    try:
        if tenant and hasattr(tenant, 'tenantconfiguration'):
            config = tenant.tenantconfiguration
            if config.default_currency:
                return config.default_currency.format_amount(float(amount))
        
        # Formato por defecto
        return f"${float(amount):,.0f}"
    except:
        return f"${float(amount):,.0f}"


@register.filter
def format_currency_simple(amount):
    """
    Formatear un monto con formato simple
    Uso: {{ amount|format_currency_simple }}
    """
    if not amount:
        return "0"
    
    try:
        return f"${float(amount):,.0f}"
    except:
        return "0"


@register.inclusion_tag('parking/tags/tax_breakdown.html')
def show_tax_breakdown(ticket):
    """
    Mostrar desglose de impuestos de un ticket
    Uso: {% show_tax_breakdown ticket %}
    """
    try:
        breakdown = ticket.get_formatted_breakdown()
        return {'breakdown': breakdown}
    except:
        return {'breakdown': None}


@register.inclusion_tag('parking/tags/company_logo.html')
def show_company_logo(size='medium'):
    """
    Mostrar logo de la empresa
    Uso: {% show_company_logo 'small' %}
    """
    return {'size': size}


@register.simple_tag
def tax_calculation_info(total_amount, tenant):
    """
    Obtener información de cálculo de impuestos
    Uso: {% tax_calculation_info total_amount request.tenant as tax_info %}
    """
    try:
        if tenant and hasattr(tenant, 'tenantconfiguration'):
            config = tenant.tenantconfiguration
            if config.apply_tax_by_default and config.default_tax_type:
                return config.calculate_tax_breakdown_from_total(float(total_amount))
        
        return {
            'subtotal': float(total_amount),
            'tax_name': None,
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': float(total_amount),
            'has_tax': False
        }
    except:
        return {
            'subtotal': float(total_amount),
            'tax_name': None,
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': float(total_amount),
            'has_tax': False
        }


@register.filter
def multiply(value, arg):
    """
    Multiplicar dos valores
    Uso: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except:
        return 0


@register.filter
def divide(value, arg):
    """
    Dividir dos valores
    Uso: {{ value|divide:arg }}
    """
    try:
        return float(value) / float(arg)
    except:
        return 0


@register.filter
def percentage(value, total):
    """
    Calcular porcentaje
    Uso: {{ value|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except:
        return 0


@register.simple_tag
def get_setting(tenant, setting_name, default=None):
    """
    Obtener una configuración específica del tenant
    Uso: {% get_setting request.tenant 'apply_tax_by_default' False %}
    """
    try:
        if tenant and hasattr(tenant, 'tenantconfiguration'):
            config = tenant.tenantconfiguration
            return getattr(config, setting_name, default)
        return default
    except:
        return default