from django.urls import path

from . import views

app_name = 'cyclecount'
urlpatterns = [
    path('begin-cycle-count/', views.begin_cycle_count, name='begin_cycle_count'),
    path('start-session/', views.start_new_session, name='start_new_session'),
    path('scan-prompt-location/<int:session_id>', views.scan_prompt_location, name='scan_prompt_location'),
    path('scan-location/<int:session_id>', views.scan_location, name='scan_location'),
    path('scan-prompt-product/<int:session_id>/<int:location_id>', views.scan_prompt_product, name='scan_prompt_product'),
    path('scan-product/<int:session_id>/<int:location_id>', views.scan_product, name='scan_product'),
]