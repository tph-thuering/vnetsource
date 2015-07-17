"""
This contains preprocessors that utilize the ManifestFile class from the manifest package.
"""

from vcimanifest import ManifestFile


def manifest_preprocessor(run, reps_per_exec=1):
    """
    This is the preprocessor for manifest files from DimRun instances.

    This calls the run.expand_executions, fills the manifest with the returned executions, fills the manifest
    with the returned run level jcd, and adds the templates.

    *NOTE* There is a temporary fix here for a shortcomming in manifest.  Namely, it was assumed that a run object
    would be passed in, however, we need to be able to pass in only ID and jcd so we can retain duplication capability.

    :param run: DimRun object to generate the manifest file for
    :type run: DimRun
    :param reps_per_exec: Replications per execution desired
    :type reps_per_exec: int
    :returns: ManifestFile
    """

    # Manifest is an immutable object (or close to it).  Once something is added it shouldn't be updated.
    # Since we know the run object will change during this process, we will add it at the end.
    manifest = ManifestFile()

    #----------- Add template files
    for f in run.template_key.dimfiles_set.all():
        manifest.add_template(
            key=f.file_type,
            content=f.content
        )

    #----------- Add executions
    try:
        (rl_jcd, executions) = run.expand_executions(reps_per_exec=reps_per_exec)
        for execution in executions:
            manifest.add_execution(execution)
    except ValueError:
        (rl_jcd, executions) = run.expand_executions(reps_per_exec=1, rl_jcd_only=True)
        for execution in run.dimexecution_set.all():
            manifest.add_execution(execution)

    #----------- Add run after updating
    #run = DimRun.objects.get(pk=run.id)

    # Originally the jcd was saved locally against the run, but the original JCD is required for duplication.
    # As such, the add_run will work, but we can't pass in the original jcd, so we have to create a slug object
    # and pass in the id and jcd that way.
    # TODO: Fix this by having add run add by id and jcd as well as by object.

    class PseudoRun:
        def __init__(self, **entries):
            self.__dict__.update(entries)

    ps_run = PseudoRun(**{"id": run.id, "jcd": rl_jcd})

    manifest.add_run(ps_run)

    return manifest