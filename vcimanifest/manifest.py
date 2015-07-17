"""
This package contains the manifest file creation and expansion code necessary to create a manifest file
and to expand it on the cluster.  This will not rely on any other part of the VecNet-CI and can live bothon the
application server and on the cluster.

The executions and runs added here should have a field called jcd.  This is a JSON Change Document.


The plan is to keep this model agnostic, but use the changes json document found at:
"""

# TODO: link json change documentation above

import json
from change_doc import JCD


class Slug(object):
    """
    This is a blank object to be filled from dictionaries.  This is useful when parsing information from a
    string ManifestFile into its components.
    """

    def __init__(self, **input_dict):
        self.__dict__.update(input_dict)
        return


class ManifestFile(object):
    """
    This is the manifest file.
    """

    def __init__(self, **kwargs):
        """
        This will create an instance of the manifest file.  Here we can define a run that this manifest file
        will represent or not.

        To define a run at instantiation, use the keyword "run".  The run has to be an obj that has several
        specific class attributes.  If it does not have these attributes, a TypeError is raised.  The list of needed
        attributed is below:
            - 'id': When using the VecNet-CI this should be the run id
            - 'base_changes': JSON style change document

        :raises: TypeError on run object not having correct attributes
        """
        self.run = None     #: This is the run the manifest file will represent

        if "run" in kwargs:
            if not self._validate_run(kwargs["run"]):
                raise TypeError("Run object must have the following attributes, ('id', 'base_changes')")
            else:
                self.run = kwargs["run"]

        self.executions = list()    #: List of executions for this manifest file
        self.templates = dict()     #: Dictionary of all template files for this manifest file
        self.version = None         #: Version of the model to use
        self.model = None           #: Mode to use

    def __iter__(self):
        """
        To aid in the creation of jobs, we include an iterator here that will iterator over the executions that
        are saved.  This will return a dictionary containing as keys the input filename and the values of those keys
        will be strings that can be written to a file.
        """
        pass

    def add_run(self, run):
        """
        If the run for this manifest file was not given at instantiation, this is how you can add the run.  If
        a run has already been specified, this will fail silently.
        """
        # TODO:  Rewrite to accept id and jcd (to create object) instead of only an object
        if self._validate_run(run) and self.run is None:
            self.run = run
        elif not self._validate_run(run):
            raise TypeError("Run object must have the following attributes, ('id', 'jcd')")

    def add_execution(self, execution):
        """
        This will add an execution to executions list.  It will first check to see if this execution is in the list,
        if not it will add it.  If it is, it will not add it, but wont alarm the sender.  This can take a single
        execution or many executions in a structure with an __iter__ function (like a list or queryset).

        The execution obj passed in should have the following attributes:
            - name: Name of the execution
            - id: When using the VecNet-CI this should be the execution id
            - xpath_changes: JSON style change document
            - replications: Number of replications of this particular execution

        :raises: TypeError when execution object does not have required attributes
        """
        if not hasattr(execution, "__iter__"):
            if not self._validate_execution(execution):
                raise TypeError("Execution must have the following attributes, ('id', 'name', 'jcd')")
            else:
                self.executions.append(execution)
        else:
            for ex in execution:
                if not self._validate_execution(ex):
                    raise TypeError("Execution must have the following attributes, ('id', 'name', 'jcd')")
                else:
                    self.executions.append(ex)
        return

    def add_template(self, key, content):
        """
        This adds a template to this manifest file.  At least one template must be added before this can be combined
        into a string or serialized.  Either key and content have to both be text or iterables.  If they are iterables
        it is assumed the order of keys maps to their contents.  The iterables must contain strings.

        :param key: The name of the template file.  For example, in EMOD this is config or campaign, in OM this is
                     usually 'input'.  This can be either an iterable or text
        :param content: The text of the template file for this manifest.  This can be either an iterable or a string
        :raises: ValueError when iterables and strings are mixed
        """
        if isinstance(key, (str, unicode)):
            if not isinstance(content, (str, unicode)):
                raise ValueError("If key is a string, content must also be a string")
            self.templates[key] = content
        elif hasattr(key, '__iter__'):
            for ndx, k in enumerate(key):
                if not isinstance(k, (str, unicode)) or not isinstance(content[ndx], (str, unicode)):
                    raise ValueError("Iterable must iterate over strings")
                else:
                    self.templates[k] = content[ndx]

    def as_json(self):
        """
        This will output the manifest file as a JSON document.  Its structure is detailed at:
        """
        # TODO: Link manifest file documentation as above

        output_dict = dict()
        output_dict['Template'] = self.templates
        output_dict['Execs'] = list()
        output_dict['Run'] = self.run.id
        output_dict['RLC'] = self.run.jcd.jcdict

        #for execution in self.executions:
        #    output_dict['Execs'].append(
        #        {
        #            'id': execution.id,
        #            'name': execution.name,
        #            'replications': execution.replications,
        #            'changes': execution.xpath_changes
        #        }
        #    )

        #  Below is the JCD version of the manifest build out.  We use the JCD.jcd (dictionary of changes) to write
        #  to the execution sections.
        for execution in self.executions:
            output_dict['Execs'].append(
                {
                    'id': execution.id,
                    'name': execution.name,
                    'replications': execution.replications,
                    'jcd': execution.jcd.jcdict
                }
            )
        return json.dumps(output_dict)

    @staticmethod
    def _validate_run(run):
        """
        This will validate a run object to make sure it has the required attributes needed by the ManifestFile.  Any
        further validation required should also go here.

        Eventually the base_changes will be phased out in favor of the JCD.
        """
        if not hasattr(run, "id"):
            return False
        #if not hasattr(run, "base_changes"):
        #    return False
        if not hasattr(run, "jcd"):
            return False

        return True

    @staticmethod
    def _validate_execution(execution):
        """
        This will validate a single execution to make sure it has the required attributes needed by the ManifestFile.
        If further validation of executions is required, it should take place here.

        Eventually the xpath_changes will be phased out in favor of the JCD.
        """
        if not hasattr(execution, "name"):
            return False
        if not hasattr(execution, "id"):
            return False
        #if not hasattr(execution, "xpath_changes"):
        #    return False
        if not hasattr(execution, "replications"):
            return False
        if not hasattr(execution, "jcd"):
            return False

        return True

    @classmethod
    def from_json(cls, content):
        """
        This will read in and parse a json manifest file and return a ManifestFile object.

        :param content: Content of the json manifest file.
        :returns: ManifestFile
        """
        try:
            file_contents = json.loads(content)
        except ValueError:
            raise ValueError("Content should be a json serializable string")

        manifest = cls()

        manifest.add_run(Slug(**{
            "id": file_contents["Run"],
            "jcd": JCD(file_contents["RLC"])
        }))

        for execution in file_contents['Execs']:
            manifest.add_execution(Slug(**{
                "id": execution["id"],
                #"xpath_changes": execution["changes"],
                "jcd": JCD(execution["jcd"]),
                "replications": execution["replications"],
                "name": execution["name"]
            }))

        template_keys = file_contents['Template'].keys()
        template_content = file_contents['Template'].values()

        manifest.add_template(template_keys, template_content)

        return manifest