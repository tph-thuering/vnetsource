"""
This contains all of the tests required to test the change class functionality
"""

from unittest import TestCase

from change_doc import JCD
from change_doc.jcd import Change


class ChangeTests(TestCase):
    """
    This class contains all of the test methods for the Change class.  Each of the five constructors will be tested:
        - __init__()
        - Change.sweep()
        - Change.arm()
        - Change.atomic()
        - Change.node()

    The other methods dealing with outputting the information stored in each change will be tested.
    """

    def testinit(self):
        """
        This will test the init constructor of the Change class.  The init constructor takes 3 optional arguments,
        each of which will fail if the wrong type of object is passed to them.  Each of these arguments will have
        to be tested.

        Parse changes will be tested separately, but this can be used as a functional test for parse change
        """

        #----- Check to see if object variables are correctly setup
        change = Change()
        self.assertIsInstance(
            change,
            Change,
            msg="Init constructor failed to create appropriate class instance"
        )

        self.assertIsInstance(
            change.change_list,
            list,
            msg="Failed to instantiate change list appropriately"
        )

        self.assertIsInstance(
            change.jcd_objects,
            list,
            msg="Failed to instantiate jcd objects list appropriately"
        )

        #------ Test to see if incorrect variable type causes ValueError
        self.assertRaises(
            ValueError,
            Change,
            ndx="5"
        )

        #------ Test to see ndx in default constructor works properly
        ndx_change = Change(ndx=5)
        self.assertEqual(
            ndx_change.ndx,
            5,
            msg="Index was not set properly"
        )

        s_change = '{"parameters/Run_Number": 5}'

        string_change = Change(change=s_change)

        self.assertEqual(
            string_change.change_list[0],
            {"parameters/Run_Number": 5},
            msg="Failed to create change via string"
        )

    def testgetconstructor(self):
        """
        We test the get_constructor method.  We send in each of the valid types and get the constructors for
        those types.  We make sure each type gets its appropriate constructor
        """

        func = Change.get_constructor("atomic")
        self.assertEqual(
            func,
            Change.atomic,
            msg="Failed to get atomic constructor"
        )

        func = Change.get_constructor("node")
        self.assertEqual(
            func,
            Change.node,
            msg="Failed to get node constructor"
        )

        func = Change.get_constructor("sweep")
        self.assertEqual(
            func,
            Change.sweep,
            msg="Failed to get sweep constructor"
        )

        func = Change.get_constructor("arm")
        self.assertEqual(
            func,
            Change.arm,
            msg="Failed to get arm constructor"
        )

        #-------- Try invalid option
        self.assertRaises(
            ValueError,
            Change.get_constructor,
            'super_type'
        )

    def testsettype(self):
        """
        We test the set_type method of the change class.  We test setting each allowed type (which overrides the
        previously saved type), and we test setting a type of a different type than string, and an invalid type
        """
        change = Change()

        #------- Test each valid type

        for type in Change.type_list:
            change.type = type
            self.assertEqual(
                change.type,
                type,
                msg="Failed to set type %s" % type
            )

        #-------- Test invalid type
        self.assertRaises(
            ValueError,
            setattr,
            change,
            "type",
            "super_type",
        )

        #-------- Test invalid object type
        self.assertRaises(
            ValueError,
            setattr,
            change,
            "type",
            5
        )

    def testsetndx(self):
        """
        We test setting the index of the change.  Since the ndx can only be set once, we test to make sure the
        ndx doesn't change when we set it again.  We also try setting an invalid object type.
        """
        change = Change()

        #-------- Test invalid object type
        self.assertRaises(
            ValueError,
            setattr,
            change,
            "ndx",
            "foo"
        )

        #--------- Test valid type and ndx
        change.ndx = 5

        self.assertEqual(
            change.ndx,
            5,
            msg="Unable to set change index"
        )

        #-------- Test setting ndx again
        change.ndx = 3000

        self.assertEqual(
            change.ndx,
            5,
            msg="Changed index after initial set"
        )

        #-------- Test deleter of ndx
        del change.ndx

        self.assertIs(
            change.ndx,
            None,
            msg="Deleter failed to delete ndx"
        )

    def testaddatomicchange(self):
        """
        Here we test the add_atomic_change method.  We attempt to add a change with an index, without and index,
        with a valid change type and with an invalid change type. We also set an ndx and try to set the ndx via
        this method to make sure that the ndx is not overridden.
        """
        change = Change()

        #---------- Test invalid change type (non-dictionary)
        self.assertRaises(
            ValueError,
            change.add_atomic_change,
            "CHANGE"
        )

        #---------- Test valid change type with ndx
        valid_change = {"parameters/Run_Number": 5}
        change.add_atomic_change(valid_change, ndx=5)
        self.assertEqual(
            change.change_list[0],
            valid_change,
            msg="Failed to set atomic change"
        )

        #---------- Test valid change with ndx after ndx already set
        change2 = Change()
        change2.ndx = 1
        change2.add_atomic_change(valid_change, ndx=5)
        self.assertEqual(
            change2.ndx,
            1,
            msg="Set index after initial set"
        )

        self.assertEqual(
            change2.change_list[0],
            valid_change,
            msg="Failed to set atomic change"
        )

    def testaddnodechange(self):
        """
        Here we test the add_node_change method of the Chnage class.  We will do this
        by trying a simple name, node pair, a name non-node pair (which should raise
        a ValueError), a list of names and a single node (which should raise a ValueError),
        a list of names and a list of nodes, a single name and a list of nodes.
        """
        change = Change()
        node1 = JCD({
            "Changes": [
                {"parameters/Run_Number": 5}
            ]
        })
        node2 = JCD({
            "Changes": [
                {"parameters/param2": 0.01}
            ]
        })

        #------ Test invalid name type, valid node type
        self.assertRaises(
            ValueError,
            change.add_node_change,
            5,
            node1
        )

        #------ Test valid name type, invalid node type
        self.assertRaises(
            ValueError,
            change.add_node_change,
            "change1",
            5
        )

        #------ Test valid name and node
        change.add_node_change('change1', node1)

        self.assertEqual(
            len(change.change_list),
            1,
            msg="More than one change added during single add node"
        )

        self.assertEqual(
            change.change_list[0],
            'change1',
            msg="Failed to add node change"
        )

        self.assertEqual(
            change.jcd_objects[0],
            node1,
            msg="Failed to add jcd object"
        )

        #------- Test single name, list of nodes

        del change
        change = Change()
        change.add_node_change('change1+change2', [node1, node2])
        self.assertEqual(
            change.jcd_objects,
            [node1, node2],
            msg="Failed to set list of nodes with single name"
        )
        self.assertEqual(
            change.change_list[0],
            'change1+change2',
            msg="Failed to set single name with list of nodes"
        )

        #-------- Test list of names and list of nodes
        del change
        change = Change()
        change.add_node_change(
            ['change1', 'change2'],
            [node1, node2]
        )
        self.assertEqual(
            change.change_list[0],
            ['change1', 'change2'],
            msg="Failed to set list of names with list of nodes"
        )
        self.assertEqual(
            change.jcd_objects,
            [node1, node2],
            msg="Failed to set list of nodes with list of names"
        )

    def testatomicconstructor(self):
        """
        This tests the atomic constructor.  We do this by testing the type checking.
        """
        #TODO: Type checking

        a_key = "parameters/Run_Number"
        a_val = 5

        a_dict = dict()
        a_dict[a_key] = a_val

        change = Change.atomic(dicts=a_dict, ndx=5)

        self.assertEqual(
            change.change_list[0],
            a_dict,
            msg="Failed to set atomic change from dictionary"
        )

        self.assertEqual(
            change.ndx,
            5,
            msg="Failed to set ndx from atomic constructor"
        )

        del change
        change = Change.atomic(xpath=a_key, value=a_val)

        self.assertEqual(
            change.change_list[0],
            a_dict,
            msg="Failed to set atomic change from xpath/value"
        )

        self.assertIs(
            change.ndx,
            None,
            msg="ndx set without argument"
        )

    def testnodeconstructor(self):
        """
        Here we test the node constructor.  We do this by checking against pass in types.

        We also test passing in different types of modes (both valid and invalid), and without modes.
        """
        # TODO: Test type validation

        name = "change1"
        node_list = [{
            "parameters/Run_Number": 5
        }]

        change = Change.node(name, node_list)

        self.assertEqual(
            change.change_list[0],
            "+change1",
            msg="Failed to add name to change list"
        )

        obj = change.jcd_objects[0]

        self.assertEqual(
            obj.name,
            "change1",
            msg="Failed to set JCD key"
        )

        self.assertEqual(
            obj.jcd["Changes"],
            node_list,
            msg="Failed to set node"
        )

        #--------- Test setting mode
        del change
        change = Change.node(name, node_list, mode='-', ndx=5)

        self.assertEqual(
            change.change_list[0],
            "-change1",
            msg="Failed to add name to change list"
        )

        obj = change.jcd_objects[0]

        self.assertEqual(
            obj.name,
            "change1",
            msg="Failed to set JCD key"
        )

        self.assertEqual(
            obj.jcd["Changes"],
            node_list,
            msg="Failed to set node"
        )

        self.assertEqual(
            change.ndx,
            5,
            msg="Failed to set index"
        )

        #------- Test invalid mode
        del change
        self.assertRaises(
            ValueError,
            Change.node,
            name=name,
            node=node_list,
            mode='p'
        )

        #------ Test invalid mode type
        self.assertRaises(
            ValueError,
            Change.node,
            name=name,
            node=node_list,
            mode=5
        )

    def testsweepconstructor(self):
        """
        Here we test the sweep constructor.  We do this by testing the type validation.

        We also test the following keyword argument pairs:
            - name, c_dict
            - name, start, stop, step
            - name, l_vals
            - name, c_dict, ndx
        """
        name = "sweep1"
        xpath = "parameters/Run_Number"
        c_dict = {
            "parameters/Run_Number": '5:10:1'
        }
        start = 5
        stop = 10
        step = 1
        l_vals = [3, 6, 7, 19]

        change = Change.sweep(name, c_dict=c_dict, ndx=5)

        self.assertEqual(
            change.change_list,
            ["sweep1"],
            msg="Failed to set change list with c_dict definition"
        )

        self.assertEqual(
            change.ndx,
            5,
            msg="Failed to set index"
        )

        obj = change.jcd_objects[0]

        self.assertEqual(
            obj.jcd["Changes"],
            [c_dict],
            msg="Failed to set sweep"
        )

        #------ Test start/stop/step
        del change
        change = Change.sweep(
            name,
            xpath=xpath,
            start=start,
            stop=stop,
            step=step
        )

        self.assertEqual(
            change.change_list,
            ["sweep1"],
            msg="Failed to set change list with start/stop/step definition"
        )

        obj = change.jcd_objects[0]

        self.assertEqual(
            obj.jcd["Changes"],
            [c_dict],
            msg="Failed to set sweep"
        )

        #-------- Test l_vals (Sweep with nonconsecutive values)
        del change
        change = Change.sweep(
            name,
            xpath=xpath,
            l_vals=l_vals
        )

        self.assertEqual(
            change.change_list,
            ["sweep1"],
            msg="Failed to set change list with start/stop/step definition"
        )

        self.assertEqual(
            change.jcd_objects[0].jcd["Changes"],
            [{
                "parameters/Run_Number": "|".join(str(x) for x in l_vals)
            }]
        )

    def testarmconstructor(self):
        """
        Here we test the arm constructor.  We test the type validation first.  After that, we test an arm with a
        compound node and two simple nodes.  This will test the entire functionality of the arm constructor.
        """
        l_names = ["change1+change2", "+change1", "-change2"]

        nodes = [
            [
                {"path/to/param1": 5}
            ],
            [
                {"path/to/param2": 0.1}
            ],
        ]

        change = Change.arm(l_names, nodes, ndx=5)

        self.assertEqual(
            change.ndx,
            5,
            msg="Failed to set ndx"
        )

        self.assertEqual(
            change.change_list[0],
            l_names,
            msg="Failed to set change list"
        )

        self.assertEqual(
            change.jcd_objects[0].jcd["Changes"],
            [ {"path/to/param1": 5} ],
            msg="Failed to set change1"
        )

        self.assertEqual(
            change.jcd_objects[0].name,
            "change1",
            msg="Failed to set JCD change name"
        )

        self.assertEqual(
            change.jcd_objects[1].jcd["Changes"],
            [ {"path/to/param2": 0.1} ],
            msg="Failed to set change2"
        )

        self.assertEqual(
            change.jcd_objects[1].name,
            "change2",
            msg="Failed to set JCD change name"
        )