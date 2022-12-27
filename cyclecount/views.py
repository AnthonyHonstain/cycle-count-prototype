from django.shortcuts import render
from .models import Location, CountSession


def begin_cycle_count(request):
    # Prompt the user to see if they want to start a cycle counting session

    return render(request, 'cyclecount/begin_cycle_count.html', {})


def start_new_session(request):
    # TODO - this is dumb, I don't want to create a new session for each page load.
    # TODO -      Note that its been a few years since I though through these full stack design issues
    current_user = request.user
    new_session = CountSession(associate=current_user)
    new_session.save()
    return render(request, 'cyclecount/start_new_session.html', {'count_session': new_session})


def scan_location(request):

    return render(request, 'cyclecount/scan_location.html', {})



