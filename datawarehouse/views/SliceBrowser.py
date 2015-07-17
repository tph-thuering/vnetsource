########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
from re import escape
from datawarehouse.mixins import JSONMixin
from datawarehouse.models import dimension_prefix, fact_prefix
from datawarehouse.cubes_config import dwmodel, engine, Session
from django.views.generic import TemplateView
from collections import OrderedDict

class SliceBrowser(JSONMixin,TemplateView):
    """This is the interface to the cube database for querying columns of data

    The cubes abstraction of the database offers dimensions on which to cut,
    but not specific coordinates along those dimensions on which to cut.
    Because of this, SliceBrowser will query for available coordinates to cut
    on.
    """

    def get_context_data(self, **kwargs):
        """Extension of the get_context_data method of the TemplateView

        This is used to query the database and setup the return_list variable
        found inherited from the JSONMixin class.  This allows the queries
        and meta dtaa to be returned to the calling browser via an ajax call.
        """
        context = super(SliceBrowser, self).get_context_data(**kwargs)

        self.return_list.clear()
        cube_name=self.request.REQUEST['cube']
        mode=self.request.REQUEST['mode']

        cube=dwmodel.cube(dwmodel.cubes[cube_name])

        if mode == 'cube':
            dim_dict = OrderedDict()
            range_dict = OrderedDict()
            level_dict = OrderedDict()
            for dim in cube.dimensions:
                if dim.name == 'user': continue
                dim_dict[dim.name] = dim.label
                if cube.dimension(dim).info is not None:
                    range_dict[dim.name] = "true"
                level_dict[dim.name] = '|'.join(dim.level_names)
            meas_type_dict = OrderedDict()
            meas_dict = OrderedDict()
            for meas in cube.measures:
                meas_dict[meas.name] = meas.name
                meas_type_dict[meas.name] = '|'.join(meas.aggregations)

            print range_dict
            self.return_list["levels"] = level_dict
            self.return_list["measure_types"] = meas_type_dict
            self.return_list["measures"] = meas_dict
            self.return_list["dimensions"] = dim_dict
            self.return_list["ranges"] = range_dict

        elif mode == 'dimension':
            dimension=self.request.REQUEST['dimension']
            level=cube.dimension(dimension).levels[0]
            self.return_list['meta']=level.attributes[0].name
            self.return_list['label']=level.label
            self.return_list['max_depth']=len(cube.dimension(dimension).levels)
            choice_list = self.get_level_choices(level,dimension)
            level_list = OrderedDict()
            for choice in choice_list:
                level_list[choice] = choice
            self.return_list["options"] = level_list
        else:
            dimension=self.request.REQUEST['dimension']
            parent_value = self.request.REQUEST['value']
            mode = self.request.REQUEST['mode']
            level_ndx = cube.dimension(dimension).level_names.index(mode)
            parent_name = cube.dimension(dimension).levels[level_ndx].attributes[0].name
            level=cube.dimension(dimension).levels[level_ndx+1]
            self.return_list['meta']=level.attributes[0].name
            self.return_list['label']=level.label
            self.return_list['depth']=level_ndx+1
            self.return_list['max_depth']=len(cube.dimension(dimension).levels)
            choice_list = self.get_level_choices(level,dimension,parent_name=parent_name,parent_value=parent_value)
            choice_list.sort()
            level_list = OrderedDict()
            for choice in choice_list:
                level_list[choice]=choice
            self.return_list["options"] = level_list

    def get_level_choices(self,level,dimension,parent_name=None,parent_value=None):
        """This gets the choices available for a given level.

        This grabs the list of the next available options on which to slice

        :param level:           Current level name.  Also current depth.
        :param dimension:       Dimension name that you are querying on.
        :param parent_name:     Name of the parent level to the current level
        :param parent_value:    Value of the parent level to the current level
        :return:                A list of strings containing the next level values on which to slice
        """

        # append dimension prefix
        dimension = dimension_prefix+dimension

        # The database name of the object:
        # if dimension == 'dim_date':
        #     db_name = 'extract(%s from timestamp)' % (level.attributes[0].name)
        #     if parent_name is not None: parent_name = 'extract(%s from timestamp)' % (parent_name)
        # else:
        db_name = level.attributes[0].name

        print db_name

        # Create the session:
        session = Session()

        # If it is the first level, there is no parent, otherwise there is and we have to 
        # go through the tree to find the choices
        if parent_name is None and parent_value is None:
            results = session.execute("select distinct(%s) from %s order by 1" % (db_name,dimension))
        else:
            results = session.execute("select distinct(%s) from %s  where %s='%s' and %s is not null order by 1" % (
                db_name,
                dimension,
                parent_name,
                parent_value,
                db_name
            ))

        # Package it up in a list to be sent back
        choices_list = list()
        for choice in results:
            choices_list.append(choice[0])
        if dimension == 'dim_date_cubes':
            choices_list = [int(x) for x in choices_list]
        return choices_list
