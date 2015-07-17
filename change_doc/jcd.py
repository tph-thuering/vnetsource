"""
This package contains the information for the JSON Change Document (JCD).
"""

import json
import itertools
from copy import deepcopy


def frange(start, stop, step):
        """This is a generator for floating point ranges

        This will generate a series of values for a floating point stop, start, and step
        """
        i = start
        while i <= stop:
            yield i
            i += step

class JCD(object):
    """
    This class represents the JSON Change Document.  This class will do validation of JCDs as well as
    help construct JCDs.

    This class is a holder for Change objects.  The Change objects are a programmatic way of
    building up a JCD.  These will be added to the change_list and JCD dictionaries.  When the
    JSON for a JCD is needed, it will iterate through these Change objects and build out the
    JCD.

    This class is also responsible for parsing from json to Change object.
    """

    factorable_types = [        #: Types that contribute to factorial expansion
            "sweep",
            "arm"
        ]

    def __init__(self, jcd=None, name=None, changes=None):
        """
        This takes a string that would be the JCD.  Django doesn't understand PostgreSQL 9.3 JSON field
        types yet, so it treats it as a string.  Here we convert that string into something more useful.
        """
        self.change_list = list()   #: Change objects in ordered list
        self._jcd = None             #: This is the JSON Change Document in dictionary format
        self._json = None           #: Hold the serialized JSON string
        self.factorables = list()   #: Lists that hold arms and sweeps (or any other factorable change)
        self.name = None            #: Optional Name parameter.  Useful for the Change object
        self.tlc = None             #: Top level Changes

        if jcd is not None:
            if isinstance(jcd, (unicode, str)):
                try:
                    jcd = json.loads(jcd)
                    if self._validate_jcd(jcd):
                        self.jcdict = jcd
                except ValueError:
                    raise ValueError("JCD provided was not valid JSON")
            elif isinstance(jcd, dict):
                if self._validate_jcd(jcd):
                    self.jcdict = jcd
                else:
                    raise ValueError("JCD was not valid")

        if name is not None and isinstance(name, (str, unicode)):
            self.name = name

        if changes is not None:
            if not isinstance(changes, list) and not all(isinstance(c, Change) for c in changes):
                raise ValueError("Changes must be a list of changes")
            self.change_list = changes
            self.jcdict = self.json

    def __str__(self):
        """
        This is the str method.

        This will output the json of the JCD.  We define this as per the tips for creating field classes.
        """
        return self.json

    def __unicode__(self):
        """
        We define this as per the general advice (tips) for creating field classes.
        """
        return unicode(self.json)

    def __repr__(self):
        """
        This is the representation string
        """
        if self.name:
            return "<change_doc.jcd.JCD for %s>" % self.name
        else:
            return "<change_doc.jcd.JCD %s>" % id(self)

    @classmethod
    def from_json(cls, json, name=None):
        """
        Alternate constructor for the JCD that accepts a json and turns it into a JCD
        """
        #TODO: Fix implementation
        return cls(json, name)

    @classmethod
    def from_changes(cls, changes, name=None):
        """
        Alternate constructor for the JCD that accepts a list of change objects
        """
        #TODO: Finish implementation
        if not isinstance(changes, list) and all(isinstance(c, Change) for c in changes):
            raise ValueError("changes must be a list of Change instances")

        return cls(name=name, changes=changes)

    @property
    def json(self):
        """
        This will take the change_list and turn it into a json.
        """
        #new_jcd = {
        #    "Changes": []
        #}
        #for change in self.change_list:
        #    new_jcd["Changes"].extend(change.change_list)
        #    for obj in change.jcd_objects:
        #        new_jcd[obj.name] = obj.jcd

        self._json = json.dumps(self.jcdict)
        return self._json

    @json.setter
    def json(self, jcd):
        """
        This method takes the json that was part of the JCD instantiation (or any json that is a valid
        JCD) and parse out the Change objects required.

        By this point, the JCD has already been validated.
        """
        jcd = json.loads(jcd)

        self.jcdict = jcd

        self._json = json.dumps(self.jcdict)

    @json.deleter
    def json(self):
        """
        This clears the json out if there is something already saved there.
        """
        if self._json is not None:
            self._json = None

    def get_factorables(self):
        """
        This method will get the lists in the changes list
        """
        self.factorables = self._get_factorables(self)
        return self.factorables

    def get_top_level_changes(self):
        """
        This method will return the top level changes as a list
        """
        self.tlc = self._get_top_level_changes(self)
        return self.tlc

    @property
    def jcdict(self):
        """
        This is the getter for the JCD (dictionary).  It regenerates its list everytime this is called.

        This keeps the JCD and JSON properties of the JCD locked with the change_list.
        """
        new_jcd = {
            "Changes": []
        }
        for change in self.change_list:
            new_jcd["Changes"].extend(change.change_list)
            for obj in change.jcd_objects:
                new_jcd[obj.name] = obj.jcdict

        self._jcd = new_jcd
        return self._jcd

    @jcdict.setter
    def jcdict(self, jcd):
        """
        This will set the jcd (dictionary version of the jcd) and split out everything into changes
        """
        if isinstance(jcd, (str, unicode)):
            self._jcd = json.loads(jcd)
            return

        for ndx, change in enumerate(jcd["Changes"]):
            change_obj = None
            if isinstance(change, dict):
                change_obj = Change.atomic(dicts=change, ndx=ndx)
            elif isinstance(change, (str, unicode)):
                if change[0] in Change.mode_list:
                    mode = change[0]
                else:
                    mode = None
                name = self._extract_objects_from_list([change])[0]

                change_obj = Change.node(
                    name=name,
                    node=jcd[name]["Changes"],
                    mode=mode,
                    ndx=ndx
                )
            else:
                if len(change) != 1:        # Means this is an arm
                    node_list = list()
                    for name in self._extract_objects_from_list(change):
                        node_list.append(jcd[name]['Changes'])
                    change_obj = Change.arm(
                        l_name=change,
                        nodes=node_list,
                        ndx=ndx
                    )
                elif len(change) == 1:      # Denotes a sweep
                    change_obj = Change.sweep(
                        name=change[0],
                        c_dict=jcd[change[0]]["Changes"][0]
                    )
            if not change_obj is None:
                self.change_list.append(change_obj)
        self._jcd = jcd

    @classmethod
    def _get_top_level_changes(cls, jcd):
        """
        This method will scan through the change list and gather the top level changes.

        Top level changes are changes before the first factorable object is defined.  Once a factorable
        is defined, all changes after that must be applied in order.

        :param jcd:  JCD to parse through
        """
        if isinstance(jcd, (str, unicode)):
            jcd = JCD.from_json(jcd)
        elif isinstance(jcd, dict):
            jcd = JCD(jcd=jcd)
        else:
            if not isinstance(jcd, JCD):
                raise ValueError("jcd Must be a valid JCD or a JCD can be created from it")

        ret_list = list()

        for change in jcd.change_list:
            if change.type in cls.factorable_types:
                break
            ret_list.append(change)

        return ret_list

    @classmethod
    def _get_factorables(cls, jcd):
        """
        This method will scan through the changes list and gather the list types useful for expansion.

        Currently this means searching for the following types:
            - Sweep
            - Arm

        The return list will be a list of tuples
        """
        ret_list = list()

        if isinstance(jcd, (str, unicode)):
            jcd = JCD.from_json(jcd)
        elif isinstance(jcd, dict):
            jcd = JCD(jcd=jcd)
        else:
            if not isinstance(jcd, JCD):
                raise ValueError("jcd Must be a valid JCD or a JCD can be created from it")

        for ndx, change in enumerate(jcd.change_list):
            if change.type == "sweep":
                ret_list.append((ndx, change.expand_sweep()))
            if change.type == "arm":
                ret_list.append((ndx, change.change_list[0]))
            elif change.type in cls.factorable_types:
                ret_list.append((ndx, change.change_list))
        return ret_list

    def is_valid(self):
        """
        This determines whether the JCD provided to the class is valid.
        """
        
        return self._validate_jcd(self.jcdict)

    @classmethod
    def _validate_jcd(cls, jcd):
        """
        This method will walk the JCD structure recursively and determine whether it is valid or not

        :param jcd: Dictionary representation of a JCD
        :returns: bool
        """

        # TODO: Make Validation more verbose

        if not 'Changes' in jcd:
            raise ValueError("%JCD is missing Changes object")

        try:
            cls._validate_list(jcd['Changes'], jcd)
        except ValueError:
            raise

        return True

    @classmethod
    def _validate_string(cls, change, jcd):
        """
        This validates whether a sub document denoted by a string change exists, and if it does, if the sub document
        is valid.

        :param change: String or unicode containing the string
        :param jcd: JCD to validate against
        :returns: bool
        """
        if change[0] == '+' or change[0] == '-':
            try:
                cls._validate_string(change.strip('+-'), jcd)
            except ValueError:
                raise
            return

        if '+' in change:
            for entry in change.split('+'):
                try:
                    cls._validate_string(entry.strip(), jcd)
                except ValueError:
                    raise
            return

        if change not in jcd:
            raise ValueError("%s object not in JCD" % change)

        try:
            cls._validate_jcd(jcd[change])
        except ValueError:
            raise

        return

    @classmethod
    def _validate_list(cls, change, jcd):
        """
        This will validate a change list.

        :param change: List containing changes to validate
        :param jcd: JCD to validate against
        :returns: bool
        """
        validict = {
            str: cls._validate_string,
            unicode: cls._validate_string,
            list: cls._validate_list
        }

        for entry in change:
            if isinstance(entry, dict):
                # There is no validation that can be done outside of knowing the model and the template
                # Perhaps we can accept as an argument a function that takes change and jcd and then
                # the dictionary version can be validated there.
                continue
            try:
                func = validict[type(entry)]
                func(entry, jcd)
            except ValueError:
                raise

        return

    @staticmethod
    def _extract_objects_from_list(l_name):
        """
        This extracts the unique object names from a list of name.  This is meant to be
        used to get object names from an arm.
        """
        name_set = set()
        for name in l_name:
            if name[0] in Change.mode_list:
                name_set.add(name.strip(''.join(Change.mode_list)))
            elif '+' in name:
                names = name.split('+')
                for n in names:
                    name_set.add(n.strip())
            else:
                name_set.add(name)

        return list(name_set)

    def expand(self):
        """
        This expand all factorables into individual JCDs
        """
        num_iter = 0
        jcd_list = list()

        tlc = self.get_top_level_changes()
        if len(tlc) == len(self.change_list):
            return self, 1, []

        #ll_change_list = deepcopy(self.change_list)
        ll_change_list = list()

        for change in self.change_list:
            if change not in tlc:
                ll_change_list.append(change)


        ll_jcd = JCD.from_changes(ll_change_list)
        new_tljcd = JCD.from_changes(tlc)

        factorables = ll_jcd.get_factorables()

        ndx_list = [f[0] for f in factorables]
        iterlist = [f[1] for f in factorables]

        iterations = itertools.product(*iterlist)

        for iteration in iterations:
            num_iter += 1
            new_jcd = deepcopy(ll_jcd)
            new_jcd.jcd_objects = list()
            for ndx, value in enumerate(iteration):
                if isinstance(value, dict):                 # This was a change for sweeps
                    new_jcd.change_list[ndx_list[ndx]] = Change.atomic(dicts=value)
                elif isinstance(value, (str, unicode)):     # This was an arm expansion
                    new_jcd.change_list[ndx_list[ndx]] = Change.node(value, ll_jcd.jcdict[value]['Changes'])
            jcd_list.append(new_jcd)

        return new_tljcd, num_iter, jcd_list


class Change(object):
    """
    This class defines a change that will be made to a template/baseline file.

    The primary purpose of this is a programmatic interface to creating a JCD.  This class will have many
    alternate constructors, allowing different types of changes to be built.  The types of changes currently supported
    are:
        ============    ===========
        Change Type     Description
        ============    ===========
        Atomic/Simple   Single value change.  Usually a simple xpath:value pair.  Entered as dictionary.
        Conceptual/Node Entered as a dictionary as well, but contains multiple changes to be applied.
        Sweeps          Entered as a list, contains a single change delimited with ':' or '|'
        Arm             Entered as a list, contains several objects, with changes
    """
    mode_list = ['+', '-', '~']     #: Supported Modes for changes
    type_list = [                   #: Supported Change Types, not meant to be changed
            'atomic',
            'node',
            'arm',
            'sweep'
        ]
    sweep_characters = [':', '|']   #: Supported Sweep characters (characters to denote sweep)

    def __init__(self, ndx=-1, change=-1, jcd=None):
        """
        This will take the index in the change list, the change list, and the JCD and parse through the pieces
        of code to fill in the class variables.

        :param ndx: Index in the change list
        :param change: List of changes for this arm
        :param jcd: The JCD object that contains all of this information
        """
        self.change_list = list()   #: Set of changes in this ARM (used for factorial expansion)
        self.jcd_objects = list()   #: Set of JCD change objects if needed (Not used for sweeps)
        self._ndx = None             #: Index in the appropriate change list
        self._type = None            #: Type of change (atomic/node/arm/sweep)

        if not isinstance(ndx, int):
            raise ValueError("ndx must be an integer")

        if ndx != -1:
            self.ndx = ndx

        if not isinstance(jcd, JCD) and jcd is not None:
            jcd = JCD(jcd)
            self._parse_change(change, jcd)
        # TODO: Add change addition

    @property
    def ndx(self):
        """
        ndx property of class
        """
        return self._ndx

    @ndx.setter
    def ndx(self, ndx):
        """
        This will set the ndx for the change.

        The ndx parameter describes when the change should take place, its order in the JCD change list, its ndx
        in that list.  Once the ndx is set, it cannot be reset.

        :param ndx:  Index of the change in the JCD change list
        :type ndx: int
        :raises: ValueError
        """
        if not isinstance(ndx, int):
            raise ValueError("ndx must be an integer")

        if self._ndx is None:
            self._ndx = ndx

        return

    @ndx.deleter
    def ndx(self):
        """
        Deleter for ndx
        """
        if self._ndx is not None:
            self._ndx = None

    @property
    def type(self):
        """
        Getter for type property
        """
        return self._type

    @type.setter
    def type(self, type):
        """
        This will set the type of the change.

        The change type should be a string.  This will internally be set via each constructor.  The types are:
            - atomic
            - node
            - arm
            - sweep

        The change type is used during factorial expansion of runs in the VecNet-CI.

        *This will override the existing type for this change, only change if you know what you're doing.*

        :param type: String containing the type name
        :raises: ValueError
        """

        if not isinstance(type, (str, unicode)) or type.lower() not in self.type_list:
            raise ValueError("type must be a string with value %s" % str(self.type_list))

        self._type = type.lower()

    @type.deleter
    def type(self):
        """
        Deleter for type
        """
        if self._type is not None:
            self._type = None

    def add_atomic_change(self, change, ndx=-1):
        """
        This adds a change to the change list.  If the ndx of the change does not exist, it is set here.

        :param change: Dictionary containing xpath/value pair to add to change list
        :raises: ValueError
        """
        if not isinstance(change, dict):
            raise ValueError("change must be a dictionary")

        if not any(c == change for c in self.change_list):
            self.change_list.append(change)

    def add_node_change(self, name, node, ndx=-1):
        """
        This adds a node change to the change list.  If the ndx of the change does not exist, it is set here.  This
        can be used to add nodes, sweeps, or even arm type changes to the change list.  If the names and nodes
        are in a list, this means that they are substitution type changes.  Therefore, the
        jcd_objects list is extended while the change object list is appended.

        :param name: Name of the node
        :param node: JCD of the node
        """
        if isinstance(name, list):
            if not all(isinstance(n, (str, unicode)) for n in name):
                raise ValueError("Names must be strings")
            self.change_list.append(name)
        elif not isinstance(name, (str, unicode)):
            raise ValueError("Name must be a string")
        else:
            self.change_list.append(name)

        if isinstance(node, list):
            if not all(isinstance(n, JCD) for n in node):
                raise ValueError("All nodes must be JCD instances")
            self.jcd_objects.extend(node)
        elif not isinstance(node, JCD):
            raise ValueError("Node must be a JCD instance")
        else:
            self.jcd_objects.append(node)

    @classmethod
    def arm(cls, l_name, nodes, ndx=-1):
        """
        This is the constructor for the arm type change.  l_name must be a list of names and node must be a list of
        lists.  Each list should contain the changes required for that node.  The order of the list of lists should
        be the same that each change appears in the arm.  For instance:

            ARM: ["mosquito1+mosquito2", "-mosquito1", "+mosquito2"]
            List of lists:
                 [ [list of changes for mosquito1], [list of changes for mosquito2] ]

        :param l_name: List of names that represent node sweeps
        :param nodes: List of lists containing dictionaries of changes
        """
        change = cls()

        if ndx != -1 and isinstance(ndx, int):
            change.ndx = ndx

        if not isinstance(l_name, list) or not all(isinstance(name, (str, unicode)) for name in l_name):
            raise ValueError("l_name must be a list of strings, received %s" % type(l_name))

        if not isinstance(nodes, list):
            raise ValueError("node must be a list of change lists, received %s" % type(nodes))
        elif not all(isinstance(node, list) for node in nodes):
            raise ValueError("Not all objects in node list are lists (Change lists)")

        names = cls._extract_names(l_name)
        node_list = list()
        for index, n in enumerate(names):
            node_dict = dict()
            node_dict["Changes"] = nodes[index]
            jcd = JCD(node_dict)
            jcd.name = n
            node_list.append(jcd)

        change.add_node_change(l_name, node_list, ndx=ndx)
        change.type = "arm"
        return change

    @classmethod
    def sweep(cls, name, **kwargs):
        """
        This is the constructor for sweep type changes.  This can take the following keywords:
            - c_dict: Should fully describe the sweep and xpath.
            - start: Starting point for numerical sweeps
            - stop: Stopping point for numerical sweeps
            - step: Step between values for numerical sweeps
            - l_vals: List of values
            - ndx: Index of the change

        :param name: Name of the sweep
        """
        ndx = None
        sweep_dict = dict()
        change = cls()

        if not isinstance(name, (str, unicode)):
            raise ValueError("name must be a string")

        if 'c_dict' in kwargs:
            if not isinstance(kwargs['c_dict'], dict):
                raise ValueError("c_dict must be a dictionary")
            sweep_dict = kwargs['c_dict']
        elif all(k in kwargs for k in ("start", "stop", "step", "xpath")):
            sweep_dict[kwargs["xpath"]] = "%s:%s:%s" % (kwargs["start"], kwargs["stop"], kwargs["step"])
        elif all(k in kwargs for k in ("xpath", "l_vals")):
            if not isinstance(kwargs["l_vals"], list):
                raise ValueError("l_vals must be a list")
            sweep_dict[kwargs["xpath"]] = "|".join(str(x) for x in kwargs["l_vals"])
        else:
            raise ValueError("Some combination of keywords must be given")

        if 'ndx' in kwargs:
            if not isinstance(kwargs['ndx'], int):
                raise ValueError("Index must be an integer")
            change.ndx = kwargs['ndx']

        jcd_dict = {"Changes": [sweep_dict], "is_sweep": True}
        jcd = JCD(jcd_dict)
        jcd.name = name

        change.type = "sweep"
        change.add_node_change([name], jcd, ndx=ndx)

        return change



    @classmethod
    def atomic(cls, xpath=None, value=None, dicts=None, ndx=-1):
        """
        This is the constructor for atomic type changes.  This can take either the xpath/value pair or
        it can take a dictionary where multiple changes are described.  If the dictionary is specified, it
        is important to note that *all changes specified in the dictionary must be order independent*.

        :param xpath: Xpath to the change
        :param value: Value of the parameter referenced by the xpath
        :param dicts: Dictionary that contains oder independent changes
        :param ndx: Index of the change in the JCD change list
        :raises: ValueError
        """
        change_dict = dict()
        if xpath is not None:
            if value is None:
                raise ValueError("If xpath is specified, so must value")
            if isinstance(xpath, (str, unicode)):
                change_dict[xpath] = value
            elif isinstance(xpath, list) and isinstance(value, list):
                for index, xpath in enumerate(xpath):
                    change_dict[xpath] = value[index]
            elif isinstance(xpath, list) and not isinstance(value, list):
                raise ValueError("If xpath is a list, values must also be a list")
            else:
                raise ValueError("xpath and value must be strings or lists of strings")

        if dicts is not None:
            if not isinstance(dicts, dict):
                raise ValueError("dicts must be a dictionary")
            else:
                change_dict = dicts

        if dicts is None and xpath is None:
            raise ValueError("Either dicts or xpath/value keywords must be specified")

        change = cls()

        if ndx != -1:
            if not isinstance(ndx, int):
                raise ValueError("index must be an integer")
            else:
                change.ndx = ndx

        change.type = "atomic"
        change.add_atomic_change(change_dict)

        return change

    @classmethod
    def node(cls, name, node, mode='+', ndx=-1):
        """
        This is the constructor for a node type change.  This takes the name of the node, the node code as a list of
        dictionaries.  Each dictionary should contain an xpath:value type change.  The value can be simple values or
        more nodes of code themselves.

        Compound nodes (ex. "mosquito1+mosquito2") must have each node defined in a separate list.  The order must be
        how they appear in the compound node definition.  For the example above, the node list will contain:
            [[list_for_mosquito1], [list_for_mosquito2]]

        :param name: Name of the node
        :param node: List of dictionaries containing changes
        :param mode: +,-,~ for append, truncate/append, or merge respectively
        :param ndx: Index of the change in the change list
        :raises: ValueError
        """
        n_changes = list()
        if mode is not None and mode not in cls.mode_list:
            raise ValueError("mode must be one of the following strings: %s" % ','.join(cls.mode_list))
        if not isinstance(name, (str, unicode)):
            raise ValueError("name must be a string")
        elif '+' in name[1:]:                           # Compound case
            names = cls._extract_names(name)
            for ndx, n in enumerate(names):
                c_dict = dict()
                c_dict[n] = JCD({
                    "Changes": node[ndx]
                },
                    name=name
                )
                n_changes.append(c_dict)
        elif name[0] in cls.mode_list:                  # Simple node with mode
            n = cls._extract_names(name)[0]
            n_changes = list()
            n_changes.append(JCD({
                "Changes": node[0]
            },
            name=name
            )
            )
        else:                                           # Simple node, default mode
            mode = ('' if mode is None else mode)
            name = "%s%s" % (mode, name)
            n_changes.append(JCD({
                "Changes": node
            },
            name=name.strip(''.join(cls.mode_list))
            )
            )
            #n_changes[name.strip(''.join(cls.mode_list))] = {
            #    "Changes": node
            #}

        change = cls()

        if ndx != -1 and isinstance(ndx, int):
            change.ndx = ndx
        elif not isinstance(ndx, int):
            raise ValueError("ndx must be an integer")

        change.add_node_change(name, n_changes, ndx=ndx)
        change.type = "node"

        return change

    @classmethod
    def get_constructor(cls, type):
        """
        This method will return the appropriate constructor for the type of change needed.  The types are listed
        in the class variable type_list.  Supported types at time of writing is:
            - atomic
            - node
            - sweep
            - arm

        :param type: String representing the change type
        """
        if not isinstance(type, (str, unicode)) or type not in cls.type_list:
            raise ValueError("type must be a string with value of %s" % "or".join(cls.type_list))

        con_dict = {
            "atomic": cls.atomic,
            "node": cls.node,
            "sweep": cls.sweep,
            "arm": cls.arm
        }

        return con_dict[type]

    def expand_sweep(self):
        """
        This will expand a sweep into different atomic changes (dictionaries)
        """
        ret_list = list()

        if self.type != "sweep":
            raise ValueError("change must be of type sweep")

        sweep_path = self.jcd_objects[0].jcdict["Changes"][0].keys()[0]
        sweep_values = self.jcd_objects[0].jcdict["Changes"][0][sweep_path]

        if ':' in sweep_values:
            start = sweep_values.split(':')[0]
            stop = sweep_values.split(':')[1]
            step = sweep_values.split(':')[2]

            try:
                start = int(start)
                stop = int(stop)
                step = int(step)
            except ValueError:
                try:
                    start = float(start)
                    stop = float(stop)
                    step = float(step)
                except ValueError:
                    raise ValueError("Start step stop must be numeric, unable to convert to int or float")

            for val in frange(start, stop, step):
                ret_list.append({sweep_path: val})

            return ret_list
        elif '|' in sweep_values:
            for val in sweep_values.split('|'):
                try:
                    ret_list.append({sweep_path: float(val)})
                except ValueError:
                    ret_list.append({sweep_path: val})
            return ret_list
        else:
            raise ValueError("Sweep did not have sweep characters, %s" % ', '.join(self.sweep_characters))

    def _parse_change(self, change, jcd):
        """
        This takes a change list and jcd and parses it into individual components.  The JCD by this point has
        already been validated

        :param change: A list containing changes
        :param jcd: JCD the changes belong to
        """
        for entry in change:
            if isinstance(entry, dict):
                continue
            elif isinstance(entry, (str, unicode)):
                changes = jcd.jcdict[entry]['Change']
                if 'is_sweep' in jcd.jcdict[entry]:
                    self.is_sweep = True
                    if len(changes) > 1:
                        raise ValueError("Numerical Sweeps must be listed separately")
                    sweep = changes[0].values()[0].split(":")
                    key = changes[0].keys()[0]
                    start = sweep[0]
                    stop = sweep[1]
                    step = sweep[2]
                    for val in frange(start, stop, step):
                        new_dict = dict()
                        new_dict[key] = val
                        self.change_list.append(new_dict)
                else:
                    self.change_list.append(entry)
                    if '+' in entry:
                        for item in entry.split('+'):
                            pass
                    self.jcd_objects.append(jcd.jcdict[entry])

        return

    @staticmethod
    def _extract_names(p_names):
        """
        This will extract node names from either a string (compound node) or a list (arm) and return
        the node names as a set.

        :param p_names: Either compound node name or arm
        :returns: Set of ordered node names
        """
        ret_set = list()
        if isinstance(p_names, (str, unicode)):
            p_names = [p_names]
        for name in p_names:
            if name[0] in Change.mode_list:
                n = name.strip(''.join(Change.mode_list))
                if n not in ret_set:
                    ret_set.append(n)
            elif '+' in name:
                names = name.split('+')
                for n in names:
                    if n not in ret_set:
                        ret_set.append(n)
            else:
                if name not in ret_set:
                    ret_set.append(name)

        return ret_set