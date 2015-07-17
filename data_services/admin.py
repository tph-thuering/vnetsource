from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from .models import *
from django.core.urlresolvers import reverse

# class DimRunAdmin(admin.ModelAdmin):
#     def executions(self,run):
#         strruns = ""
#         for run in DimExecution.objects.filter(run_key = run.id):
#             strruns += '<a href="/admin/data_services/dimexecution/' + str(run.id) + '">' + str(run.id) + "</a> "
#         return strruns
#     executions.allow_tags = True
#     list_display = ("id", "name", "experiment_key", "executions")
#     search_fields = ("id", "name", "description")
#     list_filter = ("is_deleted","experiment_key__user_key")
#     raw_id_fields = ('experiment_key',) #"location_key")
#     ordering = ('-id', )#'-experiment_key',)
# admin.site.register(DimRun, DimRunAdmin)

class DimExecutionAdmin(admin.ModelAdmin):
    def replication_ids(self, execution):
        strruns = ""
        for run in DimReplication.objects.filter(execution_key = execution.id):
            strruns += '<a href="/admin/data_services/dimreplication/' + str(run.id) + '">' + str(run.id) + "</a> "
        return strruns
    replication_ids.allow_tags = True
    list_display = ("id", "name", "run_key",)# "replications", "replication_ids")
    raw_id_fields = ('run_key',)
admin.site.register(DimExecution, DimExecutionAdmin)

class DimUserAdmin(admin.ModelAdmin):
  list_display = ("id", "username")
admin.site.register(DimUser, DimUserAdmin)

class DimReplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "execution_key", "time_started", "time_completed", "status", "status_text")
admin.site.register(DimReplication, DimReplicationAdmin)

class DimTemplateAdmin(admin.ModelAdmin):
    def files(self,template):
        strruns = ""
        #print template_id
        #template = DimTemplate.objects.get(pk = template)
        for obj in template.dimfiles_set.all():
            strruns += '<a href="/admin/data_services/dimfiles/' + str(obj.id) + '">' + str(obj.id) + "</a> "
        return strruns
    files.allow_tags = True
    list_display = ("id", "template_name", "version", "files","active")
    search_fields = ("id", "template_name", "description")
    #list_filter = ("user_key", "is_deleted")
    #ordering = ('-id', )
admin.site.register(DimTemplate, DimTemplateAdmin)

admin.site.register(DimFiles)

class DimBaselineAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "last_modified")
    search_fields = ("id", "name", "description")
    list_filter = ("user", )
admin.site.register(DimBaseline,DimBaselineAdmin)

class DimBinfilesAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "description", "version", "file_hash")
admin.site.register(DimBinFiles, DimBinfilesAdmin)

class DimLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "admin007", "admin0", "admin1", "admin2", "admin3", "geom_key")
    fields = ("admin007", "admin0", "admin1", "admin2", "admin3", "geom_key")
    search_fields = ("id", "admin007", "admin0", "admin1", "admin2", "admin3")
    ordering = ('admin0', )
admin.site.register(DimLocation, DimLocationAdmin)

class SimulationGroupAdmin(admin.ModelAdmin):
    def simulations(self, sim_group):
        string = ""
        sims = sim_group.simulations.all()
        if len(sims) > 25:
            string += '<a href="/admin/data_services/simulation/?group__id__exact=' + str(sim_group.id) + '">View All</a>'
        else:
            for obj in sims:
                string += '<a href="/admin/data_services/simulation/' + str(obj.id) + '">' + str(obj.id) + "</a> "
        return string
    simulations.allow_tags = True
    list_display = ("id", "simulations",)

admin.site.register(SimulationGroup, SimulationGroupAdmin)

class SimulationAdmin(admin.ModelAdmin):
    def files(self,simulation):
        strfiles = ""
        #print template_id
        #template = DimTemplate.objects.get(pk = template)
        for obj in simulation.input_files.all():
            strfiles += '<a href="/admin/data_services/simulationinputfile/' + str(obj.id) + '">' + str(obj.name) + "</a> "
        for obj in simulation.simulationoutputfile_set.all():
            strfiles += '<a href="/admin/data_services/simulationoutputfile/' + str(obj.id) + '">' + str(obj.name) + "</a> "
        return strfiles
    files.allow_tags = True

    def results(self,simulation):
        return "<a href=\"%s\">%s</a>" % (reverse("ts_om_viz.SimulationView", args=(simulation.id,)), simulation.id)
    results.allow_tags = True

    list_display = ("id", "status", "model", "version", "files", "results", )
    search_fields = ("id", "status", "model", "version", "group__id")
    list_filter = ("version", "group__submitted_by")


admin.site.register(Simulation, SimulationAdmin)
admin.site.register(SimulationOutputFile)
admin.site.register(SimulationInputFile)
admin.site.register(GisBaseTable, gis_admin.GeoModelAdmin)

class DimChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "type", "file_name")
    search_fields = ("id", "title", "type")

admin.site.register(DimChannel, DimChannelAdmin)