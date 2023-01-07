from django.urls import path

from cyclecount.views import individualcount_workflow, sessionreview

app_name = 'cyclecount'
urlpatterns = [
    path('begin-cycle-count/', individualcount_workflow.begin_cycle_count, name='begin_cycle_count'),
    path('start-session/', individualcount_workflow.start_new_session, name='start_new_session'),
    path('scan-prompt-location/<int:session_id>', individualcount_workflow.scan_prompt_location, name='scan_prompt_location'),
    path('scan-location/<int:session_id>', individualcount_workflow.scan_location, name='scan_location'),
    path('scan-prompt-product/<int:session_id>/<int:location_id>', individualcount_workflow.scan_prompt_product, name='scan_prompt_product'),
    path('scan-product/<int:session_id>/<int:location_id>', individualcount_workflow.scan_product, name='scan_product'),

    path('list_active_sessions/', sessionreview.list_active_sessions, name='list_active_sessions'),
    path('session_review/<int:session_id>', sessionreview.session_review, name='session_review'),
    path('finalize_session/<int:session_id>', sessionreview.finalize_session, name='finalize_session'),
]