from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.index, name='index'),

    # Clientes
    path('api/clients',          views.clients,       name='clients'),
    path('api/clients/<str:phone>', views.client_detail, name='client_detail'),

    # Entregas
    path('api/deliveries',                    views.deliveries,       name='deliveries'),
    path('api/deliveries/<str:delivery_id>',  views.delivery_detail,  name='delivery_detail'),

    # Calendario
    path('api/calendar', views.calendar, name='calendar'),

    # Optimizador
    path('api/optimize', views.optimize, name='optimize'),

    # Config
    path('api/config', views.config, name='config'),
]
