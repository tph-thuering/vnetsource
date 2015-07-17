from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.core.urlresolvers import reverse_lazy
from .models import Quota


class CreateQuota(CreateView):
    """
    View for creating quotas.
    """
    model = Quota
    success_url = reverse_lazy("list_quotas")
    template_name = 'job_services/quota.html'


class DeleteQuota(DeleteView):
    """
    View for deleting quotas.
    """
    model = Quota
    success_url = reverse_lazy("list_quotas")
    template_name = 'job_services/delete.html'


class ListQuotas(ListView):
    """
    View for listing job quotas.
    """
    model = Quota
    template_name = 'job_services/list.html'


class UpdateQuota(UpdateView):
    """
    View for updating quotas.
    """
    model = Quota
    success_url = reverse_lazy("list_quotas")
    template_name = 'job_services/quota.html'

