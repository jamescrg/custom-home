
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from apps.tasks.models import Task
from apps.tasks.forms import TaskForm
from apps.folders.models import Folder
from apps.folders.folders import select_folders
from apps.folders.folders import get_task_folders


@login_required
def index(request):

    user_id = request.user.id

    folders = get_task_folders(request, user_id)

    selected_folders = select_folders(request, 'tasks')

    active_folder_id = request.session.get('active_folder_id')

    if active_folder_id:
        active_folder = get_object_or_404(Folder, pk=active_folder_id)
    else:
        active_folder = None

    if selected_folders:
        for folder in selected_folders:
            tasks = Task.objects.filter(folder_id=folder.id)
            tasks = tasks.order_by('status', 'title')
            folder.tasks = tasks

    if active_folder:
        active_folder.tasks = Task.objects.filter(
            folder_id=active_folder.id).order_by('status', 'title')

    context = {
        'page': 'tasks',
        'folders': folders,
        'selected_folders': selected_folders,
        'active_folder': active_folder,
    }

    return render(request, 'tasks/content.html', context)


@login_required
def activate(request, id):
    request.session['active_folder_id'] = id
    return redirect('/tasks/')


@login_required
def status(request, id, origin='tasks'):
    task = get_object_or_404(Task, pk=id)
    if task.status == 1:
        task.status = 0
    else:
        task.status = 1
    task.save()
    return redirect(origin)


@login_required
def add(request):

    if request.method == 'POST':
        task = Task()
        task.user_id = request.user.id
        folder = get_object_or_404(Folder, pk=request.POST.get('folder_id'))
        task.folder = folder
        task.title = request.POST.get('title')
        task.title = task.title[0].upper() + task.title[1:]
        task.save()
        return redirect('tasks')


@login_required
def edit(request, id):

    user_id = request.user.id

    if request.method == 'POST':

        try:
            task = Task.objects.filter(pk=id).get()
        except ObjectDoesNotExist:
            raise Http404('Record not found.')

        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.user_id = user_id
            task.title = task.title[0].upper() + task.title[1:]
            task.save()

        return redirect('tasks')

    else:

        task = get_object_or_404(Task, pk=id)
        folders = get_task_folders(request, user_id)
        selected_folder = folders.filter(id=task.folder.id).get()

        form = TaskForm(instance=task, initial={'folder': selected_folder.id})
        form.fields['folder'].queryset = folders

        context = {
            'page': 'tasks',
            'edit': True,
            'folders': folders,
            'action': f'/tasks/{id}/edit',
            'form': form,
        }

        return render(request, 'tasks/content.html', context)


@login_required
def clear(request, folder_id):
    tasks = Task.objects.filter(folder_id=folder_id, status=1)
    for task in tasks:
        task.delete()
    return redirect('/tasks/')
