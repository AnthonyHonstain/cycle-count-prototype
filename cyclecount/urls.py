from django.urls import path

from . import views

app_name = 'cyclecount'
urlpatterns = [
    path('begin-cycle-count/', views.begin_cycle_count, name='begin_cycle_count'),
    path('start-session/', views.start_new_session, name='start_new_session'),
    path('scan-location/', views.scan_location, name='scan_location'),
]