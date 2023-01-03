from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from .models import Location, Product, CountSession, IndividualCount, Inventory, CycleCountModification


def begin_cycle_count(request: HttpRequest) -> HttpResponse:
    # Prompt the user to see if they want to start a cycle counting session
    return render(request, 'cyclecount/begin_cycle_count.html', {})


def start_new_session(request: HttpRequest) -> HttpResponseRedirect:
    # TODO - this is dumb, I don't want to create a new session for each page load.
    # TODO -      Note that its been a few years since I though through these full stack design issues
    current_user = request.user
    new_session = CountSession(created_by=current_user)
    new_session.save()
    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_location', args=(new_session.id,)))


def scan_prompt_location(request: HttpRequest, session_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    return render(request, 'cyclecount/scan_prompt_location.html', {'session': session})


def scan_location(request: HttpRequest, session_id: int) -> HttpResponseRedirect:
    session = get_object_or_404(CountSession, pk=session_id)
    # TODO - How to I deal with invalid location scans
    #  I can visualize the behavior I want, but unsure on how to do it in Django.
    #  This will probably be generic behavior for both location and product scan (validation and user suggestions)
    location = Location.objects.filter(description=request.POST['location-barcode']).first()
    if location is None:
        return render(request, 'cyclecount/scan_prompt_location.html',
                      {'session': session, 'error_message': "Invalid location"})
    # TODO - the back button in the brower was triggering MultiValueDictKeyError
    #  https://stackoverflow.com/questions/5895588/django-multivaluedictkeyerror-error-how-do-i-deal-with-it
    #  ANSWER: the name on the attribute in the form was different from what I was trying to get from the POST dict key
    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))


def scan_prompt_product(request: HttpRequest, session_id: int, location_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    location = get_object_or_404(Location, pk=location_id)
    return render(request, 'cyclecount/scan_prompt_product.html', {'session': session, 'location': location})


def scan_product(request: HttpRequest, session_id: int, location_id: int) -> HttpResponseRedirect:
    session = get_object_or_404(CountSession, pk=session_id)
    location = get_object_or_404(Location, pk=location_id)

    product = Product.objects.filter(sku=request.POST['sku']).first()
    if product is None:
        return render(request, 'cyclecount/scan_prompt_product.html', {
            'session': session, 'location': location, 'error_message': "Invalid location"
        })
    current_user = request.user

    individual_count = IndividualCount(
        associate=current_user, session=session, location=location, product=product,
        state=IndividualCount.CountState.ACTIVE
    )
    individual_count.save()

    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))


def list_active_sessions(request: HttpRequest) -> HttpResponse:
    # Going to start with just getting sessions created by the user, once I decide
    # on how to approach multi-tenant, this will surely change.
    current_user = request.user
    count_sessions = CountSession.objects.filter(created_by=current_user, final_state__isnull=True)
    return render(request, 'cyclecount/list_sessions.html', {'count_sessions': count_sessions})


def session_review(request: HttpRequest, session_id: int) -> HttpResponse:
    count_session = get_object_or_404(CountSession, pk=session_id)

    individual_counts = (IndividualCount.objects
                         .filter(session=count_session)
                         .select_related('associate', 'location', 'product'))

    # For each (location,product) get its current qty. Also roll up the count based on the cycle count.
    location_quantities = {}
    for individual_count in individual_counts:
        key = (individual_count.location, individual_count.product)
        if key not in location_quantities:
            inventory = Inventory.objects.filter(location=individual_count.location,
                                                 product=individual_count.product).first()
            inventory_qty = inventory.qty if inventory is not None else 0
            location_quantities[key] = {
                'location': individual_count.location,
                'product': individual_count.product,
                'cyclecount_qty': 0,
                'qty': inventory_qty
            }
        location_quantities[key]['cyclecount_qty'] += 1

    context = {
        'count_session': count_session,
        'location_quantities': location_quantities,
        'individual_counts': individual_counts,
    }
    return render(request, 'cyclecount/session_review.html', context)


def finalize_session(request: HttpRequest, session_id: int) -> HttpResponseRedirect:
    count_session = get_object_or_404(CountSession, pk=session_id)
    current_user = request.user

    # TODO - need to wrap this in a transactions, we don't want to have partial changes.
    #   A session can be processed (and inventory modifications made) at most ONCE.
    count_session.final_state = request.POST['choice']
    count_session.completed_by = current_user
    count_session.final_state_datetime = timezone.now()
    count_session.save()

    individual_counts = IndividualCount.objects.filter(session=count_session)

    # Modify inventory for everything in the session
    location_quantities = {}
    for individual_count in individual_counts:
        key = (individual_count.location, individual_count.product)
        if key not in location_quantities:
            location_quantities[key] = 0
        location_quantities[key] += 1

    for (location, product) in location_quantities:
        inventory = Inventory.objects.filter(location=location, product=product).first()
        if inventory is None:
            Inventory(location=location, product=product, qty=location_quantities[(location, product)]).save()
        else:
            inventory.qty = location_quantities[(location, product)]
            inventory.save()

        # TODO - add columns (product, old qty, new qty) to this, need to modify the DB.
        CycleCountModification(session=count_session, location_id=location, associate=current_user).save()

    return HttpResponseRedirect(reverse('cyclecount:list_active_sessions'))
