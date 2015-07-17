"""
This contains the EMOD specific manifest.  This inherits from the ManifestFile base class.

The reintegration code here is both model and version specific.  As such, each version should
have it's own reintegration code and the reintegration method should select, based on a keyword
in the manifest file, which method to use.
"""

import json
from manifest import ManifestFile
from json_merging.merge_tools import merge_list


class EMODManifestFile(ManifestFile):
    """
    This is the EMOD Specific manifest file.

    This inherits the ability to read in from JSON.  From that, it can split out fully
    specified config and campaign files to be used by EMOD as inputs.

    The code that lives in this class is specifically related to splitting executions
    back out from the manifest file.
    """

    config = None           #: Config dictionary
    campaign = None         #: Campaign dictionary
    template_files = [      #: The required template files for an EMOD simulation
        'config.json',
        'campaign.json'
    ]

    @classmethod
    def split_executions_15(cls, manifest, template):
        """
        This will merge the changes from executions into a config and campaign file from a manifest
        for EMOD version 1.5.

        :params manifest: ManifestFile instance
        :params template: Dictionary containing the config.json and campaign.json
        :yields: Tuples containing (execution_id, num_replications, execution_config.json, execution_campaign.json)
        """
        for execution in manifest.executions:
            exec_id = execution.id
            exec_changes = execution.jcd.jcdict
            template = merge_list(template, exec_changes)
            yield exec_id, execution.replications, json.dumps(template['config.json']), json.dumps(template['campaign.json'])

    def split_executions(self):
        """
        This generator method will split the manifest file into individual executions and return execution id,
        config.json (as json), and campaign.json (as json).

        This first checks to see if a manifest file has been created or read in with templates, executions,
        and a run.  It also checks to make sure the required template files are in the template dict.

        Before returning specific executions, we merge in the run level changes.
        """
        if self.run is None or self.executions == [] or self.templates == {}:
            raise ValueError("You must read or create a manifest file with runs and executions")

        if not all(x in self.templates.keys() for x in self.template_files):
            raise ValueError("Template must contain keys for config.json and campaign.json")

        # -------- We create a single dictionary that holds both as the xpath specified within EMOD manifests
        # -------- refer to the file as the first path.
        template = dict()
        template['config.json'] = json.loads(self.templates['config.json'])
        template['campaign.json'] = json.loads(self.templates['campaign.json'])

        self.version='1.5'
        rlcl = self.run.jcd.jcdict
        template = merge_list(template, rlcl)

        split_dict = {
            '1.5': self.split_executions_15
        }

        for execution_tuple in split_dict[self.version](self, template):
            yield execution_tuple
