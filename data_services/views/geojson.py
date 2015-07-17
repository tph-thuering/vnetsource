from django.views.generic import TemplateView
from datawarehouse.mixins import JSONMixin
from django.http import Http404, HttpResponse
from data_services.adapters import EMOD_Adapter
from data_services.models import DimLocation, DimRun
import json


class GeoJsonView(JSONMixin, TemplateView):
    """
    This class is the the view responsible for returning geojsons from the VECNet CI Data Warehouse.  This url takes
    an number, which should be a valid location index.  If it is not a valid location index, a 404 is returned, if it
    is valid, the geojson for that shape in the Data Warehouse is returned.
    """

    def get_context_data(self, **kwargs):
        self.return_list.clear()
        # context = super(GeoJsonView, self).get_context_data(**kwargs)

        if 'run' in self.request.GET:
            run = DimRun.objects.get(id=int(self.request.GET['run']))
            if not run:
                raise Http404('Run with id %s does not exist' % self.request.GET['run'])
            location = run.location_key
        elif 'location' in self.request.GET:
            location = DimLocation.objects.filter(pk=int(self.request.GET['location']))
            if not location.exists():
                raise Http404('Location with id %s does not exist' % self.request.GET['location'])
            location = location[0]
        else:
            raise Http404('Keywords location or run must be specified')

        adapter = EMOD_Adapter()
        self.return_list = json.loads(adapter.fetch_geojson(location=location.id))

        return