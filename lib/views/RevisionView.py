# Copyright 2013 University of Notre Dame
# Developers:
#   James Domingo

from subprocess import check_output, CalledProcessError
from django.views.generic import TemplateView

class RevisionView(TemplateView):
    # TODO Add class docstring
    # TODO Add method docstring(s)
    # TODO Consider additional comments
    template_name = 'lib/revision.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionView, self).get_context_data()

        try:
            context['svn_revision'] = check_output('svnversion')
        except OSError, e:
            context['svnversion_error'] = e.strerror + (' (exit code %d)' % e.errno)
        except CalledProcessError, e:
            context['svnversion_error'] = e.output + (' (return code %d)' % e.returncode)

        return context
