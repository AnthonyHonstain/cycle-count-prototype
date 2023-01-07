from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from cyclecount.models import Location, Product, CountSession, IndividualCount


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
    if session.final_state is not None:
        return HttpResponseNotFound()
    return render(request, 'cyclecount/scan_prompt_location.html', {'session': session})


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
    # TODO - the back button in the brower was triggering MultiValueDictKeyError
    #  https://stackoverflow.com/questions/5895588/django-multivaluedictkeyerror-error-how-do-i-deal-with-it
    #  ANSWER: the name on the attribute in the form was different from what I was trying to get from the POST dict key
    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))


def scan_prompt_product(request: HttpRequest, session_id: int, location_id: int) -> HttpResponse:
    session = get_object_or_404(CountSession, pk=session_id)
    if session.final_state is not None:
        return HttpResponseNotFound()
    location = get_object_or_404(Location, pk=location_id)
    return render(request, 'cyclecount/scan_prompt_product.html', {'session': session, 'location': location})


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
    current_user = request.user

    individual_count = IndividualCount(
        associate=current_user, session=session, location=location, product=product,
        state=IndividualCount.CountState.ACTIVE
    )
    individual_count.save()

    return HttpResponseRedirect(reverse('cyclecount:scan_prompt_product', args=(session.id, location.id)))
