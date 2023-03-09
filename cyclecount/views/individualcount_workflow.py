import structlog
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from cyclecount.models import Location, Product, CountSession, IndividualCount


log = structlog.get_logger(__name__)


@login_required
def begin_cycle_count(request: HttpRequest) -> HttpResponse:
    # Prompt the user to see if they want to start a cycle counting session
    return render(request, 'cyclecount/begin_cycle_count.html', {})


@login_required
def start_new_session(request: HttpRequest) -> HttpResponseRedirect:
    # TODO - this feel dumb, do I want to create a new session for each page load?
    # TODO -      Note that its been a few years since I though through these full stack design issues
    new_session = CountSession(created_by=request.user)
    new_session.save()
    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_location', args=(new_session.id,)))


@login_required
def scan_prompt_location(request: HttpRequest, session_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    if session.final_state is not None:
        return HttpResponseNotFound()
    return render(request, 'cyclecount/scan_prompt_location.html', {'session': session})


@login_required
def scan_location(request: HttpRequest, session_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    if session.final_state is not None:
        return HttpResponseNotFound()
    # TODO - How to I deal with invalid location scans
    #  I can visualize the behavior I want, but unsure on how to do it in Django.
    #  This will probably be generic behavior for both location and product scan (validation and user suggestions)
    location = Location.objects.filter(description=request.POST['location-barcode']).first()
    if location is None:
        return render(request, 'cyclecount/scan_prompt_location.html',
                      {'session': session, 'error_message': "Invalid location"})

    log.info('scan_location', session_id=session_id, location=location.id, associate=request.user.id)
    # TODO - the back button in the browser was triggering MultiValueDictKeyError
    #  https://stackoverflow.com/questions/5895588/django-multivaluedictkeyerror-error-how-do-i-deal-with-it
    #  ANSWER: the name on the attribute in the form was different from what I was trying to get from the POST dict key
    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))


@login_required
def scan_prompt_product(request: HttpRequest, session_id: int, location_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    if session.final_state is not None:
        return HttpResponseNotFound()
    location = get_object_or_404(Location, pk=location_id)
    return render(request, 'cyclecount/scan_prompt_product.html', {'session': session, 'location': location})


@login_required
def scan_product(request: HttpRequest, session_id: int, location_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    if session.final_state is not None:
        return HttpResponseNotFound()
    location = get_object_or_404(Location, pk=location_id)

    product = Product.objects.filter(sku=request.POST['sku']).first()
    if product is None:
        return render(request, 'cyclecount/scan_prompt_product.html', {
            'session': session, 'location': location, 'error_message': "Invalid location"
        })

    individual_count = IndividualCount(
        associate=request.user, session=session, location=location, product=product,
        state=IndividualCount.CountState.ACTIVE
    )
    individual_count.save()

    log.info('scan_product individual_count created',
             session_id=session_id, location=location.id, product=product.id, associate=request.user.id)

    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))
