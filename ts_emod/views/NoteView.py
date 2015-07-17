########################################################################################################################
# VECNet CI - Prototype
# Date: 6/18/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from data_services.adapters.EMOD import EMOD_Adapter
from django.shortcuts import redirect
from lib.templatetags.base_extras import set_notification
from django.views.generic.edit import CreateView

from ts_emod.forms import NoteCreateForm


class NoteView(CreateView):
    """Class to implement Note Creation View
    """
    form_class = NoteCreateForm
    #model = Note
    template_name = 'ts_emod/note_create.html'
    fields = ['text']

    def get_context_data(self, **kwargs):
        context = super(NoteView, self).get_context_data(**kwargs)
        context['run_id'] = self.kwargs['run_id']
        return context


# TODO Convert to CBV
def saveNote(request, run_id, note_id=None ):
    """Function to save Note DB Objects
    """
    if request.method == 'POST':
        #note = Note(text=request.POST.get('text'), run_key_id=run_id)
        #note.save()

        if run_id == None:
            run_id = request.POST.get('run_id')

        adapter = EMOD_Adapter(request.user.username)
        note_id = adapter.save_note(run_id, note=request.POST.get('text'))

    if note_id != None:
        set_notification('alert-success','<strong>Success!</strong> You have successfully saved the note.', request.session)
    else:
        set_notification('alert-error','<strong>Error!</strong> There was a problem saving the note.', request.session)
    return redirect(request.environ['HTTP_REFERER'])


# TODO Convert to CBV
def deleteNote(request, note_id):
    """Function to delete Species DB Objects
    """
    try:
        note_to_delete = Note.objects.get(id=note_id)
        note_to_delete.delete()
        set_notification('alert-success','<strong>Success!</strong> You have successfully deleted the note.', request.session)
    except:
        print 'Error deleting note with id: %s' % note_id
        set_notification('alert-error','<strong>Error!</strong> There was a problem deleting the note.', request.session)
    return redirect('ts_emod_run_browse')

## An instance of NoteView
#
# - redirect to run in save method
note_create_view = NoteView.as_view()

