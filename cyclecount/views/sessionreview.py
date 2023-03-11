import operator
from functools import reduce
from typing import Tuple, Dict

import structlog
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from cyclecount.models import CountSession, IndividualCount, Inventory, CycleCountModification


log = structlog.get_logger(__name__)


@login_required
def list_active_sessions(request: HttpRequest) -> HttpResponse:
    # Going to start with just getting sessions created by the user, once I decide
    # on how to approach multi-tenant, this will surely change.
    current_user = request.user
    count_sessions = CountSession.objects.filter(created_by=current_user, final_state__isnull=True)
    return render(request, 'cyclecount/list_sessions.html', {'count_sessions': count_sessions})


@login_required
def session_review(request: HttpRequest, session_id: int) -> HttpResponse:
    count_session = get_object_or_404(CountSession, pk=session_id)

    individual_counts = (IndividualCount.objects
                         .filter(session=count_session)
                         .select_related('associate', 'location', 'product'))

    # For each (location,product) get its current qty. Also roll up the count based on the cycle count.
    location_quantities: Dict[Tuple[int, int], Dict] = {}
    for individual_count in individual_counts:
        key = (individual_count.location.id, individual_count.product.id)
        if key not in location_quantities:
            location_quantities[key] = {
                'location': individual_count.location,
                'product': individual_count.product,
                'cyclecount_qty': 0,
                'qty': 0
            }
        location_quantities[key]['cyclecount_qty'] += individual_count.qty

    if location_quantities:  # We don't want to look up inventory if there are zero IndividualCounts
        query = reduce(
            operator.or_,
            (Q(location_id=loc, product_id=prod) for (loc, prod) in location_quantities.keys())
        )
        for inventory in Inventory.objects.filter(query):
            location_quantities[(inventory.location_id, inventory.product_id)]['qty'] = inventory.qty

    log.info(
        'session_review summary',
        individual_counts_count=len(individual_counts),
        location_quantities_count=len(location_quantities)
    )
    context = {
        'count_session': count_session,
        'location_quantities': location_quantities,
        'individual_counts': individual_counts,
    }
    return render(request, 'cyclecount/session_review.html', context)


@login_required
def finalize_session(request: HttpRequest, session_id: int) -> HttpResponse:
    current_user = request.user

    with transaction.atomic():
        count_session_lock = CountSession.objects.select_for_update().get(pk=session_id)
        if count_session_lock is None:
            return HttpResponseNotFound()

        if count_session_lock.final_state is not None:
            raise Exception(f'CountSession id:{count_session_lock.id} in invalid state of: {count_session_lock.final_state}')

        count_session_lock.final_state = request.POST['choice']
        count_session_lock.completed_by = current_user
        count_session_lock.final_state_datetime = timezone.now()
        count_session_lock.save()

        if request.POST['choice'] == CountSession.FinalState.CANCELED:
            return HttpResponseRedirect(reverse('cyclecount:list_active_sessions'))

        individual_counts = IndividualCount.objects.filter(session=count_session_lock)

        # Modify inventory for everything in the session
        location_quantities = {}
        for individual_count in individual_counts:
            key = (individual_count.location, individual_count.product)
            if key not in location_quantities:
                location_quantities[key] = 0
            location_quantities[key] += 1

        for (location, product) in location_quantities:
            old_qty = 0
            inventory = Inventory.objects.filter(location=location, product=product).first()
            if inventory is None:
                inventory = Inventory(location=location, product=product, qty=location_quantities[(location, product)])
                inventory.save()
            else:
                old_qty = inventory.qty
                inventory.qty = location_quantities[(location, product)]
                inventory.save()

            CycleCountModification(session=count_session_lock, location=location, product=product, old_qty=old_qty,
                                   new_qty=inventory.qty, associate=current_user).save()

    return HttpResponseRedirect(reverse('cyclecount:list_active_sessions'))
