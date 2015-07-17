from django.contrib import admin
from .models import *

class QuotaAdmin(admin.ModelAdmin):
    list_display = ("user", "max_per_month", "max_per_run", "cluster")
    fields = ("user", "max_per_month", "max_per_run", "cluster")
    search_fields = ("user", "cluster")
    ordering = ('user', )

admin.site.register(Quota, QuotaAdmin)

class SubmittedJobsAdmin(admin.ModelAdmin):
    list_display = ("user", "cluster", "number_of_jobs", "date")

admin.site.register(SubmittedJobs,SubmittedJobsAdmin)