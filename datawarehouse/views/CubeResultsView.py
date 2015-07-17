########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
"""
This module contains the CubeResultsView class.
"""

# import statements
import operator
from django.views.generic import TemplateView
from datawarehouse.mixins import JSONMixin
from datawarehouse.models import dimension_prefix, fact_prefix
from datawarehouse.cubes_config import dwmodel, engine
import cubes, string, itertools, pdb
from collections import OrderedDict

# Helper functions for the view

def getTopLevel(cube, dimName):
    """This method returns the top level of the given dimension. For instance,
    consider a cube with the dimension location which has the levels region, country,
    and place. If dimName is location, this returns region.

    :param cube: The current cube.
    :param dimName: The current dimension, such as location.
    """
    try: return cube.dimension(dimName).hierarchy().levels_for_depth(1)[0].name
    except: return "level not found"


def getCurrentLevel(cube, dimName, path):
    """This method returns the current level of the given path. For instance,
    consider a cube where the dimension location has the levels region, country,
    and place. If dimName is location and path is [location, ], this returns region.
    If path is [location, region] this returns country.

    :param cube: The current cube.
    :param dimName: The current dimension, such as location.
    :param path: A list of the current path, such as [location, region].
    """
    try: return cube.dimension(dimName).hierarchy().levels_for_path(path)[-1].name
    except: return "level not found"


def getNextLevel(cube, dimName, path):
    """This method returns the level below the dimension name. For instance,
    consider a cube where the dimension location has the levels region, country,
    and place. If dimName is location and path is [location, ], this returns country.
    If path is [location, region] this returns place.

    :param cube: The current cube.
    :param dimName: The current dimension, such as location.
    :param path: A list of the current path, such as [location, region].
    """
    try: return cube.dimension(dimName).hierarchy().next_level(cube.dimension(dimName).hierarchy().levels_for_path(path)[-1].name).name
    except: "level not found"


def sortDictByMultipleKeys(mydict, arguments):
    """This method accepts a list of dictionaries and returns the list sorted by
    dictionary keys. The keys are passed as a list via arguments.  For example:
    the dictionaries in the list contain the keys 'year', 'day', and 'month'. If
    arguments is ['year', 'month'], then this returns the list sorted by year and month.

    :param mydict: A list of dictionaries
    :param arguments: A list of keys to sort on
    """
    mydict.sort(key=operator.itemgetter(*arguments)) # sorts the list in place
    return mydict

class CubeResultsView(JSONMixin, TemplateView):
    """CubeResultsView is an extension of the generic TemplateView in Django.
    It is used to generate results of a datawarehouse request. The results
    are returned as a JSON object.
    """
    queryset = None                                                         #: determines the queryset to use
    error = {}                                                              #: error flags
    
    def get_context_data(self, **kwargs):
        """This method is responsible for creating and returning the
        context data.
        """
        context = super(CubeResultsView, self).get_context_data(**kwargs)   # call the super
        
        # initialize variables
        mode = None                 # mode can be raw or aggregated
        aggregations = None         # a list of the aggregations requested
        agg_paths = []              # the aggregation paths requested
        agg_dict = {}               # holds the aggregations and their respective paths
        num_slices = None           # the number of slices performed
        cube_name = None            # the requested cube name
        cut_list=list()             # a list of the cuts to be performed on the cube
        hashDict = {}               # a dictionary containing slices by dimension
        hashList = []               # a list of just the slices, without dimension information
        hashProduct = []            # a cartesian product of slices
        self.error.clear()          # make sure self.error is intially empty
        
        # fetch data from GET
        if 'num_slices' in self.request.GET:                                
            num_slices = self.request.REQUEST['num_slices']
        if 'cube' in self.request.GET:
            cube_name = self.request.REQUEST['cube']
        if 'drilldim' in self.request.GET:
            aggregations = self.request.REQUEST['drilldim'].split("|")
        if 'drillpath' in self.request.GET:
            agg_paths = self.request.REQUEST['drillpath'].split("|")
        if 'mode' in self.request.GET:
            mode = self.request.REQUEST['mode']
        
        # check for errors in the GET data
        if aggregations == None or aggregations == "":
            self.error['aggregations_error'] = "You must select an aggregation dimension." 
        if num_slices == "" or num_slices == None:                         
            self.error['slices_error'] = "You must provide the number of slices"  
        if cube_name == None or cube_name == "":                            
            self.error['cube_error'] = "You must provide the cube name"
            
        # couple the aggregations with their paths
        pathLen = len(agg_paths)
        for i in range(0, len(aggregations)):
            if i < pathLen:
                agg_dict[aggregations[i]] = agg_paths[i]
            else:
                agg_dict[aggregations[i]] = ""
                
        # For each slice, get the path and dimension and create a cut 
        for x in range(0,int(num_slices)):
            # initialize the variables. from_path and to_path allow range slicing.
            dimension = None
            from_path = None
            to_path = None
            path = None

            #get the path and dimension
            if 'dimension_'+str(x) in self.request.GET:
                dimension=(self.request.REQUEST['dimension_'+str(x)])   # get the requested dimension
            if 'path_'+str(x) in self.request.GET:
                path=(self.request.REQUEST['path_'+str(x)].split('-'))  # get the requested path

            # check for errors
            if dimension == None or dimension == "":
                self.error['dimension'+str(x)+'_error'] = "You must provide a dimension for each slice."
            if path == None or path == "":
                self.error['path'+str(x)+'_error'] = "You must provide a path for each slice."
            
            # if a dimension and corresponding path were found, create the cut
            if 'path'+str(x)+'_error' not in self.error and 'dimension'+str(x)+'_error' not in self.error:
                if len(path) > 1:                                       # if the path has multiple paths, perform a range cut
                    from_path = path[0].split("|")
                    to_path = path[1].split("|")
                    cut = cubes.RangeCut(dimension,from_path,to_path)   # define the cut
                else:
                    cut = cubes.PointCut(dimension,path[0].split("|"))     # define the cut
                
                # add the cut to the appropriate list
                if dimension in hashDict:
                    hashDict[dimension].append(cut)
                else:
                    hashDict[dimension] = [cut]

        # if 'REMOTE_USER' in self.request.META and self.request.META['REMOTE_USER'] != "":
        #     user = self.request.META['REMOTE_USER']
        # else:
        #     user = None
        #
        # if user:
        #     cut = cubes.SetCut('testuser',['public',user])
        #     hashDict['user'] = [cut]
        # else:
        #     cut = cubes.PointCut('testuser', ['public'])
        #     hashDict['user'] = [cut]

        for k, v in hashDict.iteritems():               # store cuts by dimension
            hashList.append(v)
        for item in itertools.product(*hashList):       # compute a cartesian product on the cuts and convert the
            hashProduct.append((list(item)))            # tuples to lists. Each list in hashProduct is a cut list         

        if self.error == {}:                                                # if there are no errors, perform the aggregations        
            # initialize variables
            results = {}                                                    # this dictionary gets serialized into the returned JSON object
            agg_result = None                                               # this holds the aggregated cubes data
            counter = 0                                                     # a counter variable
            cube = dwmodel.cube(dwmodel.cubes[cube_name])                   # Create the cube
            # cube.key = cube.mappings['id']                                  # enforce cube mappings
            conn = engine.connect()                                         # Connect to the sqlalchemy engine
            workspace = cubes.create_workspace("sql",dwmodel,engine=engine,
                                               dimension_prefix=dimension_prefix,
                                               fact_prefix=fact_prefix) # get a workspace
            browser = workspace.browser(cube)                               # get a browser
            cell = cubes.Cell(cube)                                         # create the cell
            
            results['slices'] = []                                          # create a holder for the slices
            # for each requested aggregation, we must perform all cuts in the cut list and generate
            # an object containing aggregated data for the cut
            if mode == 'raw':
                result = {}
                for cutlist in hashProduct:
                    sliceString = ""                                        # create a string containing information about the cuts
                                                                            # this string will be added to measure names
                    # loop over the cuts and create the sliceString and the level
                    for cut in cutlist:
                        sliceString += "_"
                        if hasattr(cut, 'path'):
                            sliceString += "|".join(cut.path)
                        elif hasattr(cut, 'paths'):
                            sliceString += "|".join(cut.paths)
                        else:
                            sliceString += "|".join(cut.from_path)
                            sliceString += "-"
                            sliceString += "|".join(cut.to_path)
                            
                        results['slices'].append(sliceString)               # add the slicestring to the results object
                    new_cell = cell.multi_slice(cutlist)                    # Slice up the cube using all of the cuts
                    raw_result = browser.facts(new_cell)                    # and get the data 
            
                    counter = 0                                             # reinitialize the counter
                        
                    # Parse the cubes data into columns which are added to a dictionary
                    for row in raw_result:
                        if counter == 0:                                    # on the first pass, create the column lists
                            for k, v in row.iteritems():
                                result[k+sliceString] = []
                            counter = counter + 1                           # and increment the counter
                        
                        for k, v in row.iteritems():                        # add the key to the appropriate column list
                            result[k+sliceString].append(v)       
                
                results['raw'] = result                                     # append this object to the dict of objects
                
                self.return_list = results                                  # set the return_list, used by JSONMixin
                        
            else:
                for a, p in agg_dict.iteritems():
                    result = {}                                                 # create an object
                    for cutlist in hashProduct:
                        level = None
                        sliceString = ""                                        # create a string containing information about the cuts
                                                                                # this string will be added to measure names
                        # loop over the cuts and create the sliceString and the level
                        for cut in cutlist:
                            sliceString += "_"
                            if hasattr(cut, 'path'):
                                sliceString += "|".join(cut.path)
                            else:
                                sliceString += "|".join(cut.from_path)
                                sliceString += "-"
                                sliceString += "|".join(cut.to_path)
                            
                            if a == cut.dimension and p == "":                      # if the aggregation variable was sliced on and no path 
                                if hasattr(cut, 'path'):                            # was specified, use the slice path to get the appropriate level
                                    level = getNextLevel(cube, a, cut.path)
                                else:
                                    level = getCurrentLevel(cube, a, cut.from_path) # path isn't a key for range cuts, so use from instead
                                                                                    # and get the current level instead of the next level
                            sliceString += "_" + str(a)         
                            if level == "level not found":                          # if there was an error getting the level, then the 
                                self.error['level'] = level                         # aggregation will not work, so return an error
                                self.return_list = self.error
                                return context
                        results['slices'].append(sliceString)                       # add the slicestring to the results object           
                        if level == None and p == "":
                            level = getTopLevel(cube, a)                            # otherwise get the first level of the aggregation variable
    
                        new_cell = cell.multi_slice(cutlist)                        # Slice up the cube using all of the cuts
                        if p == "":
                            agg_result = browser.aggregate(new_cell, drilldown=[a]) # and aggregate the data
                        else:
                            level = p
                            agg_result = browser.aggregate(new_cell, drilldown=[(a,'default',p)])
                        # add information about the x-axis to the object
                        if str(a) == level:                                     
                            result['level'] = level                          
                        else:
                            result['level'] = str(a + "." + level)              

                        # get the levels. results are sorted by level up to the requested level depth
                        arguments = []                              # create an empty list for the levels
                        for x in cube.dimension(a).levels:          # loop over the levels for this cube
                            arguments.append(x.attributes[0].ref()) # append the level to the arguments list
                            if x.name == level:                     # if we've reached the requested level, then break
                                break
    
                        counter = 0
                        newlist = []                        # create an empty list
                        for row in agg_result:              # create a list copy of the cubes result object
                            newlist.append(row)
                        newlist = sortDictByMultipleKeys(newlist, arguments)    # sort the result object by the levels
                        # Parse the cubes data into columns which are added to a dictionary
                        for row in newlist:
                            if counter == 0:                                    # on the first pass, create the column lists
                                for k, v in row.iteritems():
                                    result[k+sliceString] = []
                                counter = counter + 1                           # and increment the counter
                            
                            for k, v in row.iteritems():                        # add the values to the appropriate column list
                                result[k+sliceString].append(v)       
                    
                    results[a] = result                                     # append this object to the dict of objects
                    
                self.return_list = results                                  # set the return_list, used by JSONMixin
        else:
            self.return_list = self.error                               # if errors were present, return them
            
        conn.close()


