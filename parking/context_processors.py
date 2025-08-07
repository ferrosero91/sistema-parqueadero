"""
Context processors para el sistema de parqueadero
"""

def tenant_context(request):
    """
    Context processor para agregar información del tenant a todos los templates
    """
    context = {}
    
    # Verificar si hay un tenant en la sesión
    if hasattr(request, 'tenant') and request.tenant:
        context['current_tenant'] = request.tenant
        
        # Agregar configuración del tenant si existe
        try:
            config = request.tenant.tenantconfiguration
            context['tenant_config'] = config
            
            # Logo de la empresa
            if config.company_logo:
                context['company_logo'] = config.company_logo.url
            else:
                context['company_logo'] = None
                
            # Moneda por defecto
            if config.default_currency:
                context['default_currency'] = config.default_currency
                context['currency_symbol'] = config.default_currency.symbol
            else:
                context['default_currency'] = None
                context['currency_symbol'] = '$'
                
            # Información de impuestos
            if config.default_tax_type and config.apply_tax_by_default:
                context['default_tax'] = config.default_tax_type
                context['tax_enabled'] = True
                context['tax_rate'] = float(config.default_tax_type.rate)
            else:
                context['default_tax'] = None
                context['tax_enabled'] = False
                context['tax_rate'] = 0
                
            # Configuración de formato
            context['thousand_separator'] = config.thousand_separator
            context['decimal_separator'] = config.decimal_separator
            
        except:
            # Si no hay configuración, usar valores por defecto
            context['tenant_config'] = None
            context['company_logo'] = None
            context['default_currency'] = None
            context['currency_symbol'] = '$'
            context['default_tax'] = None
            context['tax_enabled'] = False
            context['tax_rate'] = 0
            context['thousand_separator'] = '.'
            context['decimal_separator'] = ','
    
    return context


def system_info(request):
    """
    Context processor para información general del sistema
    """
    return {
        'system_name': 'SoluPark',
        'system_version': '1.0.0',
        'system_description': 'Sistema de Estacionamiento',
    }