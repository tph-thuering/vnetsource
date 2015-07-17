from django.db import models
from django.contrib.auth.models import User
from data_services.models import DimRun
from . import cluster_id


cluster_choices = tuple([(cluster, cluster) for cluster in cluster_id.ALL_KNOWN])


class RunProvider(models.Model):
    """
    Associates a run to a provider. When runs are submitted to a cluster for execution, the provider is stored in this
    table for future retrieval. This ensures that once a run is submitted with a particular provider, that same provider
    is always used for that run.
    """
    provider = models.CharField(max_length=256)
    run = models.ForeignKey(DimRun)


class Job(models.Model):
    """
    Represents a Job object. Jobs are associated to runs (data_services.models.DimRun) and are used to send runs to
    the cluster to be processed.
    """
    run = models.ForeignKey(DimRun)
    cluster = models.CharField(choices=cluster_choices, max_length=cluster_id.MAX_LENGTH)


class Quota(models.Model):
    """
    Sets the maximum number of jobs a user can run on a cluster.
    """
    user = models.ForeignKey(User)
    max_per_month = models.IntegerField()  # maximum number of jobs per month
    max_per_run = models.IntegerField()  # maximum number of jobs per run
    cluster = models.CharField(choices=cluster_choices, max_length=cluster_id.MAX_LENGTH)

    class Meta:
        unique_together = ('user', 'cluster')


class SubmittedJobs(models.Model):
    """
    Associates a user and cluster to a number of submitted jobs. Used to calculate the number of jobs a user has
    submitted to a given cluster.
    """
    cluster = models.CharField(choices=cluster_choices, max_length=cluster_id.MAX_LENGTH)
    date = models.DateTimeField()
    number_of_jobs = models.IntegerField()
    user = models.ForeignKey(User)


class Manifest(models.Model):
    """
    Stores a manifest file associated with a given run.
    """
    run = models.ForeignKey(DimRun)
    manifest = models.TextField()

