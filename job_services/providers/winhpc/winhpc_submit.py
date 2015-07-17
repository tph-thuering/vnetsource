from third_party import winhpclib

def winhpc_submit(run_id,
                  submitted_by,
                  start_simgroup_path,
                  host,
                  user,
                  pswd,
                  alt_ingest_url = None):
    try:
        server = winhpclib.Server(host, user, pswd)
        job = winhpclib.Job(server)
        job.properties["FailOnTaskFailure"] = "True"
        job.properties["Name"] = "(%s) %s " % (submitted_by, run_id)
        job.properties["Priority"] = "AboveNormal"
        job.properties["MaxCores"] = "1"
        job.properties["MaxNodes"] = "1"
        # http://msdn.microsoft.com/en-us/library/microsoft.hpc.scheduler.ischedulerjob.maximumnumberofnodes(v=vs.85).aspx
        # If you set this property, you must set AutoCalculateMax to false;
        # otherwise, the maximum number of nodes that you specified will be ignored.
        job.properties["AutoCalculateMax"] = False
        job.create()

        job.save_environment( { "ALT_INGEST_URL" : alt_ingest_url,
                                "JOB_SUBMITTER"  : submitted_by,
                                "DIMRUN_NUMBER"     : run_id,
                                } )

        remote_vals = job._server.get_properties( job._get_url() + "/EnvVariables" )
        print "DBG: The following environment variables were set: ", remote_vals

        task = job.create_task()
        task.properties["Commandline"] = \
            "c:\\python27\\python.exe  %s --run_id %s --username %s" % (start_simgroup_path, run_id, submitted_by)
        task.properties["Name"] = "Run EMOD model"
        task.properties["WorkDirectory"] = "C:\\"
        task.create()
        job.submit(user, pswd)
    except winhpclib.Error as error:
        print "winhpc_submit failed: %s" % error
        return -1
    print "%s" % job.id
    return job.id