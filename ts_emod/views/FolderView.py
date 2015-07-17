########################################################################################################################
# VECNet CI - Prototype
# Date: 02/19/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <rjones29@nd.edu>
########################################################################################################################

from data_services.models import DimBaseline, DimUser, Folder
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from lib.templatetags.base_extras import set_notification


def folder_save(request):
    """ Function to save Folder DB Objects
    - Takes the form data posted and uses it to make a new folder
    - folder_id is the new folder's parent
    """

    if request.POST.get('folder-name') == '':
        set_notification('alert-error', '<strong>Error!</strong> Please name the folder.',
                         request.session)
        return redirect("ts_emod_scenario_browse")

    if request.method == 'POST':
        if request.POST.get('folder_id') is not None and request.POST.get('folder_id') != '':
            parent = Folder.objects.get(pk=int(request.POST.get('folder_id')))
        else:
            parent = None

        folder = Folder(name=request.POST.get('folder-name'),
                        description=request.POST.get('folder-description'),
                        parent=parent,
                        user=DimUser.objects.get(username=request.user.username),
                        sort_order=0)
        folder.save()

    if folder.id is not None:
        set_notification('alert-success',
                         '<strong>Success!</strong> You have successfully created the folder %s.' % folder.name,
                         request.session)
    else:
        set_notification('alert-error', '<strong>Error!</strong> There was a problem saving the folder.',
                         request.session)
    return redirect("ts_emod_scenario_browse", folder_id=str(folder.id))


def folder_delete(request, folder_id):
    """ Function to delete Folder DB Objects
        Input: folder_id: id of folder to be deleted
        - Only deletes folder if it's empty (displays error if not)
    """

    my_parent = 0
    folder_to_delete = Folder.objects.get(id=folder_id)
    if folder_to_delete.parent is not None:
        my_parent = str(folder_to_delete.parent.id)
    else:
        my_parent = None

    test = folder_to_delete.delete()
    if test is True:
        set_notification('alert-success', '<strong>Success!</strong> You have successfully deleted the folder.',
                         request.session)
    elif test == 'NotEmpty':
        set_notification('alert-error', '<strong>Error!</strong> You cannot delete the folder because it is not empty. '
                                        'Please remove all simulations and folders from it before deleting.',
                         request.session)
        # go to folder that wasn't deleted because it wasn't empty - show user what's in there
        return redirect("ts_emod_scenario_browse", folder_id=str(folder_to_delete.id))
    else:
        print 'Error deleting folder with id: %s' % folder_id
        set_notification('alert-error', '<strong>Error!</strong> There was a problem deleting the folder.',
                         request.session)

    if my_parent is None:
        # return to the home/root folder
        return redirect("ts_emod_scenario_browse")
    else:
        # return to the parent folder
        return redirect("ts_emod_scenario_browse", folder_id=str(my_parent))


def folder_move(request, folder_id, item_id, item_type):
    """ Function to "move" a scenario or folder into a Folder
        Input folder_id: folder_id: id of folder target
        Input item_id: id of item moving into folder
        Input item_type: whether item is scenario (0) or folder (1)
\    """
    if folder_id == '0':
        target = None
    else:
        target = Folder.objects.get(id=folder_id)

    try:
        if item_type == "1":
            # item is a folder
            item = Folder.objects.get(id=item_id)
            item.parent = target
        else:
            item = DimBaseline.objects.get(id=item_id)
            item.folder = target
        item.save()
        return HttpResponse(True, mimetype="text/plain")
    except:
        return HttpResponse(False, mimetype="text/plain")


def folder_rename(request, folder_id, name):
    """ Function to rename Folder DB Objects
        Input: folder_id: id of folder to be renamed
    """

    try:
        folder_to_rename = Folder.objects.get(id=folder_id)
        folder_to_rename.name = name.split('(')[0].strip()  # Remove sim count and leading/trailing whitespace
        folder_to_rename.save()
        return HttpResponse(name, mimetype="text/plain")
    except:
        return HttpResponse('False', mimetype="text/plain")
