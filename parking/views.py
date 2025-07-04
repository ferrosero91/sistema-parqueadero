# Python standard library
from datetime import datetime, timedelta

# Django core
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now

# Django database
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import Extract, TruncDate

# Django views
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from django.views.generic.edit import DeleteView

# Local imports
from .forms import CategoryForm, ParkingLotForm, ParkingTicketForm
from .models import ParkingLot, ParkingTicket, VehicleCategory, Caja


@login_required
def pagina_inicial(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'registration/login.html')


class ParkingLotUpdateView(UpdateView):
    model = ParkingLot
    template_name = 'parking/parking_lot_form.html'
    fields = ['nombre', 'nit', 'telefono', 'direccion']
    success_url = reverse_lazy('dashboard')


class CategoryListView(ListView):
    model = VehicleCategory
    template_name = 'parking/category_list.html'


class CategoryCreateView(CreateView):
    model = VehicleCategory
    form_class = CategoryForm
    template_name = 'parking/category_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        messages.success(self.request, "Categoría creada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Hubo un error al crear la categoría.")
        return super().form_invalid(form)


class VehicleEntryView(CreateView):
    model = ParkingTicket
    form_class = ParkingTicketForm
    template_name = 'parking/vehicle_entry.html'
    success_url = reverse_lazy('print-ticket')

    def form_valid(self, form):
        try:
            category = form.cleaned_data['category']
            if category.name.upper() == 'MOTOS':
                cascos = self.request.POST.get('cascos', 0)
                form.instance.cascos = int(cascos)
            response = super().form_valid(form)
            self.request.session['ticket_id'] = str(self.object.id)
            return response
        except IntegrityError:
            messages.error(self.request, 'Este vehículo ya se encuentra en el estacionamiento.')
            return self.form_invalid(form)


@login_required
def vehicle_exit(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        ticket = ParkingTicket.objects.filter(
            placa__iexact=identifier,
            exit_time=None
        ).first()

        if ticket:
            try:
                # Registrar la salida
                ticket.exit_time = timezone.now()
                ticket.amount_paid = ticket.calculate_fee()
                ticket.save()

                # Para solicitudes AJAX (primer formulario)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'amount': ticket.amount_paid,
                        'duration': ticket.get_duration(),
                        'placa': ticket.placa,
                        'entry_time': ticket.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'ticket_id': str(ticket.id)
                    })

            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': str(e)}, status=500)
                messages.error(request, f'Error: {str(e)}')
                return redirect('vehicle-exit')

        # Si no se encuentra el ticket
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)
        messages.error(request, 'Vehículo no encontrado')
        return redirect('vehicle-exit')

    # Para solicitudes GET
    placa = request.GET.get('placa', '')
    return render(request, 'parking/vehicle_exit.html', {
        'placa': placa,
    })


@login_required
def print_exit_ticket(request):
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        amount_received = request.POST.get('amount_received')

        if ticket_id and amount_received:
            try:
                ticket = ParkingTicket.objects.get(id=ticket_id)
                amount_received = float(amount_received)
                amount_paid = float(ticket.amount_paid)
                change = amount_received - amount_paid

                parking_lot = ParkingLot.objects.first()

                return render(request, 'parking/print_exit_ticket.html', {
                    'ticket': ticket,
                    'parking_lot': parking_lot,
                    'amount_received': amount_received,
                    'change': change,
                    'current_time': timezone.now(),
                })
            except ParkingTicket.DoesNotExist:
                messages.error(request, 'Ticket no encontrado')
                return redirect('dashboard')
            except ValueError:
                messages.error(request, 'El monto recibido no es válido')
                return redirect('vehicle-exit')
            except Exception as e:
                messages.error(request, f'Error al imprimir ticket: {str(e)}')
                return redirect('dashboard')

    messages.warning(request, 'No se especificó un ticket para imprimir')
    return redirect('dashboard')


@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Definir el rango de los últimos 7 días
    start_date = today - timedelta(days=7)
    
    # Obtener tickets que entraron en los últimos 7 días
    recent_tickets = ParkingTicket.objects.filter(
        entry_time__date__gte=start_date,
        entry_time__date__lte=today
    )

    # Obtener ingresos de tickets que salieron en los últimos 7 días
    recent_revenue = ParkingTicket.objects.filter(
        exit_time__date__gte=start_date,
        exit_time__date__lte=today,
        exit_time__isnull=False,
        amount_paid__isnull=False
    )

    # Obtener vehículos activos (sin salida)
    active_vehicles = ParkingTicket.objects.filter(
        exit_time__isnull=True
    ).select_related('category')

    # Estadísticas diarias de los últimos 7 días
    daily_stats = ParkingTicket.objects.filter(
        exit_time__date__gte=start_date,
        exit_time__date__lte=today,
        exit_time__isnull=False,
        amount_paid__isnull=False
    ).values('exit_time__date').annotate(
        revenue=Sum('amount_paid'),
        count=Count('id')
    ).order_by('exit_time__date')

    # Estadísticas por categoría de los últimos 7 días
    category_stats = ParkingTicket.objects.filter(
        exit_time__date__gte=start_date,
        exit_time__date__lte=today,
        exit_time__isnull=False,
        amount_paid__isnull=False
    ).values('category__name').annotate(
        count=Count('id'),
        revenue=Sum('amount_paid')
    )

    # Estadísticas generales
    stats = {
        'daily': {
            'total_vehicles': recent_tickets.count(),  # Contar vehículos que entraron en los últimos 7 días
            'total_revenue': recent_revenue.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0  # Ingresos de tickets que salieron en los últimos 7 días
        },
        'category': category_stats,
        'active_vehicles': active_vehicles.count(),
        'active_vehicles_list': active_vehicles
    }

    context = {
        'stats': stats,
        'daily_stats': [
            {
                'date': stat['exit_time__date'].strftime('%d/%m/%Y'),
                'revenue': stat['revenue'] or 0,
                'count': stat['count'] or 0,
            }
            for stat in daily_stats
        ],
        'current_time': timezone.now()
    }

    return render(request, 'parking/dashboard.html', context)
@login_required
def print_ticket(request):
    ticket_id = request.GET.get('ticket_id') or request.session.get('ticket_id')
    
    if ticket_id:
        try:
            ticket = ParkingTicket.objects.get(id=ticket_id)
            parking_lot = ParkingLot.objects.first()
            
            if 'ticket_id' in request.session:
                del request.session['ticket_id']
            
            return render(request, 'parking/print_ticket.html', {
                'ticket': ticket,
                'parking_lot': parking_lot,
                'is_reprint': bool(request.GET.get('ticket_id')),
                'current_time': timezone.now(),
                'duration': ticket.get_duration() if ticket.exit_time else ticket.get_current_duration(),
                'current_fee': ticket.amount_paid if ticket.exit_time else ticket.calculate_current_fee()
            })
        except ParkingTicket.DoesNotExist:
            messages.error(request, 'Ticket no encontrado')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error al imprimir ticket: {str(e)}')
            return redirect('dashboard')
    
    messages.warning(request, 'No se especificó un ticket para imprimir')
    return redirect('vehicle-entry')


class ReportView(TemplateView):
    template_name = 'parking/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manejo de fechas
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if not start_date or not end_date:
            today = now()
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            start_date = datetime.strptime(f"{start_date} 00:00:00", '%Y-%m-%d %H:%M:%S')
            end_date = datetime.strptime(f"{end_date} 23:59:59", '%Y-%m-%d %H:%M:%S')

        # Obtener tickets completados
        tickets = ParkingTicket.objects.filter(
            exit_time__isnull=False,
            exit_time__range=(start_date, end_date)
        ).exclude(amount_paid__isnull=True)

        # Resumen general
        summary = tickets.aggregate(
            total_vehicles=Count('id'),
            total_revenue=Sum('amount_paid'),
            avg_duration=Avg(F('exit_time') - F('entry_time')),
            avg_revenue=Avg('amount_paid')
        )

        if summary['avg_duration'] is not None:
            summary['avg_duration'] = summary['avg_duration'].total_seconds() / 3600

        # Estadísticas por categoría
        category_stats = []
        for stat in tickets.values('category__name').annotate(
            count=Count('id'),
            revenue=Sum('amount_paid'),
        ).order_by('-count'):
            category_tickets = tickets.filter(category__name=stat['category__name'])
            durations = [
                (ticket.exit_time - ticket.entry_time).total_seconds() / 3600
                for ticket in category_tickets
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            stat['avg_duration'] = avg_duration
            category_stats.append(stat)

        # Estadísticas diarias
        daily_stats = list(tickets.annotate(
            date=TruncDate('exit_time')
        ).values('date').annotate(
            count=Count('id'),
            revenue=Sum('amount_paid')
        ).order_by('date'))

        # Vehículos más frecuentes
        frequent_vehicles = tickets.values('placa').annotate(
            visits=Count('id'),
            total_spent=Sum('amount_paid')
        ).order_by('-visits')[:10]

        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'summary': summary,
            'category_stats': category_stats,
            'daily_stats': daily_stats,
            'frequent_vehicles': frequent_vehicles,
            'parking_lot': ParkingLot.objects.first()
        })
        return context


@login_required
def company_profile(request):
    parking_lot = ParkingLot.objects.first()

    if request.method == 'POST':
        form = ParkingLotForm(request.POST, instance=parking_lot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Información de la empresa actualizada correctamente.')
            return redirect('company_profile')
    else:
        form = ParkingLotForm(instance=parking_lot)

    return render(request, 'parking/company_profile.html', {'form': form})


def custom_logout(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')


def category_edit(request, pk):
    category = get_object_or_404(VehicleCategory, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect('category-list')
        else:
            messages.error(request, "Hubo un error al actualizar la categoría.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'parking/category_edit.html', {'form': form})


def validate_plate(request, plate):
    exists = ParkingTicket.objects.filter(
        placa__iexact=plate,
        exit_time__isnull=True
    ).exists()
    return JsonResponse({'exists': exists})


class CategoryDeleteView(DeleteView):
    model = VehicleCategory
    success_url = reverse_lazy('category-list')
    template_name = 'parking/category_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoría eliminada exitosamente')
        return super().delete(request, *args, **kwargs)

@login_required
def cash_register(request):
    # Determinar si el usuario es vendedor
    is_vendedor = request.user.groups.filter(name='Vendedor').exists()

    # Manejo de fechas
    today = timezone.now().date()  # Fecha actual (23/03/2025)

    if is_vendedor:
        # Vendedores solo ven el día actual
        start_date = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end_date = start_date + timedelta(days=1)
    else:
        # Administradores pueden filtrar por fechas
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = timezone.make_aware(datetime.strptime(f"{start_date_str} 00:00:00", '%Y-%m-%d %H:%M:%S'))
                end_date = timezone.make_aware(datetime.strptime(f"{end_date_str} 23:59:59", '%Y-%m-%d %H:%M:%S'))
            except ValueError:
                # Si las fechas no son válidas, usar el día actual
                start_date = timezone.make_aware(datetime.combine(today, datetime.min.time()))
                end_date = start_date + timedelta(days=1)
        else:
            # Si no se proporcionan fechas, usar el día actual
            start_date = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            end_date = start_date + timedelta(days=1)

    # Obtener los tickets del período con salida registrada y monto pagado
    tickets = ParkingTicket.objects.filter(
        exit_time__gte=start_date,
        exit_time__lt=end_date,
        exit_time__isnull=False,  # Solo tickets con salida
        amount_paid__isnull=False  # Solo tickets con monto pagado
    )
    total_income = sum(ticket.amount_paid or 0 for ticket in tickets)

    # Buscar o crear el registro de Caja para el período
    caja_date = start_date.date()
    caja_queryset = Caja.objects.filter(fecha=caja_date, tipo='Ingreso')

    if caja_queryset.exists():
        # Si hay múltiples registros, consolidarlos en uno solo
        if caja_queryset.count() > 1:
            caja = caja_queryset.first()
            total_monto = sum(c.monto for c in caja_queryset)
            caja.monto = total_monto
            caja.descripcion = f'Ingresos del período {start_date.date()} a {end_date.date()} (consolidado)'
            caja.save()
            caja_queryset.exclude(id=caja.id).delete()
        else:
            # Si solo hay un registro, usarlo
            caja = caja_queryset.first()
            # Actualizar el monto y la descripción
            caja.monto = total_income
            caja.descripcion = f'Ingresos del período {start_date.date()} a {end_date.date()}'
            caja.save()
    else:
        # Si no existe un registro, crearlo
        caja = Caja.objects.create(
            fecha=caja_date,
            tipo='Ingreso',
            monto=total_income,
            descripcion=f'Ingresos del período {start_date.date()} a {end_date.date()}',
            dinero_inicial=0.00  # Inicialmente 0, se actualizará con el formulario
        )

    # Calcular el dinero esperado (dinero_inicial + total_income)
    dinero_esperado = float(caja.dinero_inicial) + float(total_income)

    # Manejar el formulario para establecer el dinero inicial (base para vueltos)
    if request.method == 'POST' and 'set_dinero_inicial' in request.POST:
        try:
            dinero_inicial = float(request.POST.get('dinero_inicial', 0))
            if dinero_inicial < 0:
                messages.error(request, 'El dinero inicial no puede ser negativo.')
            else:
                caja.dinero_inicial = dinero_inicial
                caja.save()
                messages.success(request, 'Dinero inicial establecido correctamente.')
            return redirect('cash_register')
        except ValueError:
            messages.error(request, 'Por favor, ingrese un valor numérico válido para el dinero inicial.')

    # Manejar el formulario para el cuadre de caja
    if request.method == 'POST' and 'realizar_cuadre' in request.POST:
        if caja.cuadre_realizado:
            messages.error(request, 'El cuadre de caja para este período ya fue realizado.')
            return redirect('cash_register')

        try:
            dinero_final = float(request.POST.get('dinero_final', 0))
            if dinero_final < 0:
                messages.error(request, 'El dinero final no puede ser negativo.')
                return redirect('cash_register')

            # Actualizar el registro de Caja
            caja.dinero_final = dinero_final
            caja.monto = total_income
            caja.descripcion = f'Ingresos del período {start_date.date()} a {end_date.date()}'
            caja.cuadre_realizado = True
            caja.save()

            messages.success(request, 'Cuadre de caja realizado con éxito.')
            return redirect('cash_register')
        except ValueError:
            messages.error(request, 'Por favor, ingrese un valor numérico válido para el dinero final.')

    # Calcular diferencia si el cuadre ya fue realizado
    diferencia = None
    diferencia_abs = None
    if caja.cuadre_realizado:
        diferencia = (caja.dinero_final - caja.dinero_inicial) - total_income
        diferencia_abs = abs(diferencia)  # Calcular el valor absoluto

    context = {
        'today': today,
        'start_date': start_date.date(),
        'end_date': (end_date - timedelta(days=1)).date(),
        'tickets': tickets,
        'total_income': total_income,
        'caja': caja,
        'dinero_esperado': dinero_esperado,
        'diferencia': diferencia,
        'diferencia_abs': diferencia_abs,
        'is_vendedor': is_vendedor,
    }
    return render(request, 'parking/cash_register.html', context)