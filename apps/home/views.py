from datetime import datetime, date, timedelta
import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from accounts.models import CustomUser
from apps.tasks.models import Task
from apps.favorites.models import Favorite
from apps.folders.models import Folder
import apps.home.google as google


@login_required
def index(request):
    user_id = request.user.id
    user = get_object_or_404(CustomUser, pk=user_id)

    # EVENTS
    # ----------------

    # check whether events have been hidden
    show_events = request.session.get('show_events', True)

    # if events are hidden, check the date they were hidden
    # if that date is less than today, show them
    if not show_events:

        # get current day
        now = datetime.now(pytz.timezone('America/New_York'))
        today = now.date()

        # get day events were previously hidden
        timestamp = int(request.session.get('events_hide_expire'))
        old_date = date.fromtimestamp(timestamp)

        # set events to shown only if today is greater than the old date
        if today > old_date:
            show_events = True
            request.session['show_events'] = True

    # if events are shown, load them
    if show_events:
        if user.google_credentials:
            events = google.get_events(user_id)
        else:
            events = None
    else:
        events = None


    # TASKS
    # ----------------

    # check whether tasks have been hidden
    show_tasks = request.session.get('show_tasks', True)

    # if tasks are hidden, check the date they were hidden
    # if that date is less than today, show them
    if not show_tasks:

        # get current day
        now = datetime.now(pytz.timezone('America/New_York'))
        today = now.date()

        # get day events were previously hidden
        timestamp = int(request.session.get('events_hide_expire'))
        old_date = date.fromtimestamp(timestamp)

        # set events to shown only if today is greater than the old date
        # and the hour on the server clock is greater than 5 am
        if today > old_date:
            show_tasks = True
            request.session['show_tasks'] = True

    # check for task_folders
    task_folders = Folder.objects.filter(
        user_id=user_id, page='tasks', home_column__gt=1)
    if task_folders:
        for folder in task_folders:
            tasks = Task.objects.filter(folder_id=folder.id).exclude(status=1)
            tasks = tasks.order_by('status', 'title')
            folder.tasks = tasks


    # FAVORITES
    # ----------------

    columns = []
    for i in range(1, 5):
        folders = Folder.objects.filter(user_id=user_id, page='favorites', home_column=i)
        folders = folders.order_by('home_rank')
        for folder in folders:
            favorites = Favorite.objects.filter(folder_id=folder.id, home_rank__gt=0)
            favorites = favorites.order_by('home_rank')
            folder.favorites = favorites
        columns.append(folders)

    context = {
        'page': 'home',
        'origin': 'home',
        'search_engine': 'google.com/search',
        'show_tasks': show_tasks,
        'task_folders': task_folders,
        'events': events,
        'show_events': show_events,
        'columns': columns,
    }

    return render(request, 'home/index.html', context)


@login_required
def toggle_events(request):
    show_events = request.session.get('show_events', True)
    if show_events:
        request.session['show_events'] = False
        request.session['events_hide_expire'] = date.today().strftime('%s')
    else:
        request.session['show_events'] = True
    return redirect('/home/')


@login_required
def toggle_tasks(request):
    show_tasks = request.session.get('show_tasks', True)
    if show_tasks:
        request.session['show_tasks'] = False
        request.session['tasks_hide_expire'] = date.today().strftime('%s')
    else:
        request.session['show_tasks'] = True
    return redirect('/home/')


@login_required
def folder(request, id, direction):
    user_id = request.user.id

    # if the stack order is being changed
    if direction == 'up' or direction == 'down':

        # get the folder to be moved
        # identify the column to which it belongs
        origin_folder = get_object_or_404(Folder, pk=id)
        origin_column = origin_folder.home_column

        # make sure the folders are sequential and adjacent
        folders = Folder.objects.filter(user_id=user_id, home_column=origin_column)
        folders = folders.order_by('home_rank')
        count = 1
        for folder in folders:
            folder.home_rank = count
            folder.save()
            count += 1

        # identify the origin rank as modified by the sequence operation
        origin_rank = origin_folder.home_rank

        # identify the destination rank
        if direction == 'up':
            destination_rank = origin_rank - 1
        if direction == 'down':
            destination_rank = origin_rank + 1

        # identify the folder to be displaced
        try:
            displaced_folder = Folder.objects.filter(
                user_id=user_id, home_column=origin_column, home_rank=destination_rank
            ).get()
        except Folder.DoesNotExist:
            displaced_folder = False

        # if a folder is being displaced, move it and the original folder
        if displaced_folder:
            origin_folder.home_rank = destination_rank
            origin_folder.save()
            displaced_folder.home_rank = origin_rank
            displaced_folder.save()

    # if the column is being changed
    if direction == 'left' or direction == 'right':

        # get the folder to be moved, along with its column and rank
        origin_folder = get_object_or_404(Folder, pk=id)
        origin_column = origin_folder.home_column

        if direction == 'left' and origin_column > 1:
            destination_column = origin_column - 1
        elif direction == 'right' and origin_column < 4:
            destination_column = origin_column + 1
        else:
            destination_column = origin_column

        # identify the bottom folder in the destination column
        # move over origin folder to destination column and place at bottom
        if destination_column != origin_column:
            bottom_folder = (
                Folder.objects.filter(user_id=user_id, home_column=destination_column)
                .order_by('-home_rank')
                .first()
            )
            bottom_rank = bottom_folder.home_rank
            origin_folder.home_column = destination_column
            origin_folder.home_rank = bottom_rank + 1

        # persist changes
        origin_folder.save()

        # resequence origin column
        # make sure the folders are sequential and adjacent
        folders = Folder.objects.filter(user_id=user_id, home_column=origin_column)
        folders = folders.order_by('home_rank')
        count = 1
        for folder in folders:
            folder.home_rank = count
            folder.save()
            count += 1

    return redirect('/home/')


@login_required
def favorite(request, id, direction):
    user_id = request.user.id

    # get the favorite to be moved
    origin_favorite = get_object_or_404(Favorite, pk=id)
    folder_id = origin_favorite.folder_id

    # make sure the favorites are sequential and adjacent
    favorites = Favorite.objects.filter(
        user_id=user_id, folder_id=folder_id, home_rank__gt=0
    )
    favorites = favorites.order_by('home_rank')

    count = 1
    for favorite in favorites:
        favorite.home_rank = count
        favorite.save()
        count += 1

    favorites = Favorite.objects.filter(
        user_id=user_id, folder_id=folder_id, home_rank__gt=0
    )
    favorites = favorites.order_by('home_rank')

    # identify the origin rank as modified by the sequence operation
    origin_favorite = get_object_or_404(Favorite, pk=id)
    origin_rank = origin_favorite.home_rank

    # identify the destination rank
    if direction == 'up':
        destination_rank = origin_rank - 1
    if direction == 'down':
        destination_rank = origin_rank + 1

    # identify the favorite to be displaced
    displaced_favorite = Favorite.objects.filter(
        user_id=user_id, folder_id=folder_id, home_rank=destination_rank
    ).first()

    # if a favorite is being displaced, move it and the original favorite
    # otherwise, we are at the end of the column, make no changes
    origin_favorite.home_rank = destination_rank
    origin_favorite.save()

    if displaced_favorite:
        displaced_favorite.home_rank = origin_rank
        displaced_favorite.save()

    return redirect('/home/')
