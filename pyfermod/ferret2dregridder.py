#! python
#

'''
Regridder for converting data between a curvilinear longitude, 
latitude grid and a rectilinear longitude, latitude grid.  
Uses the ESMP interface to ESMF to perform the regridding. 

@author: Karl Smith
'''

import numpy
import ESMP

class Ferret2DRegridder(object):
    '''
    Regridder for regridding data between a 2D curvilinear grid, where 
    the longitude and latitude of each grid corner and/or center point 
    is explicitly defined, and a 2D rectilinear grid, where the grid 
    corners are all intersections of a given set of strictly increasing 
    longitudes with a set of strictly increasing latitudes.  The 
    rectilinear grid centers are the the intersections of averaged 
    consecutive longitude pairs with averaged consecutive latitude pairs.  

    For these grids, the center point [i,j] is taken to be the center 
    point of the quadrilateral defined by connecting consecutive corner 
    points in the sequence (corner_pt[i,j], corner_pt[i+1,j], 
    corner_pt[i+1,j+1], corner_pt([i,j+1], corner_pt[i,j]).

    Uses the ESMP interface to ESMF to perform the regridding.  Prior 
    to calling any instance methods in the Ferret2DRegridder class, the 
    ESMP module must be imported and ESMP.ESMP_Initialize() must have 
    been called.  When a Ferret2DRegridder instance is no longer needed, 
    the finalize method of the instance should be called to free ESMP 
    resources associated with the instance.  When ESMP is no longer 
    required, the ESMP.ESMP_Finalize() method should be called to free 
    all ESMP and ESMF resources.
    '''


    def __init__(self):
        '''
        Initializes to an empty regridder.  The ESMP module must be 
        imported and ESMP.ESMP_Initialize() called prior to calling
        any methods in this instance.
        '''
        # tuples giving the shape of the grid (defined by number of cells)
        self.__curv_shape = None
        self.__rect_shape = None
        # ESMP_Grid objects describing the grids
        self.__curv_grid = None
        self.__rect_grid = None
        # ESMP_Field objects providing the source or regridded data
        self.__curv_dest_field = None
        self.__curv_src_field = None
        self.__rect_dest_field = None
        self.__rect_src_field = None
        # handles to regridding operations between the fields/grids
        self.__curv_to_rect_handles = { }
        self.__rect_to_curv_handles = { }


    def createCurvGrid(self, center_lons, center_lats, center_ignore=None,
                       corner_lons=None, corner_lats=None, corner_ignore=None):
        '''
        Create the curvilinear grid as an ESMP_Grid using the provided center
        longitudes and latitudes as the grid center points, and, if given, 
        the grid corner longitudes and latitudes as the grid corner points.
        Curvilinear data is assigned to the center points.  Grid point
        coordinates are assigned as coord[i,j] = ( lons[i,j], lats[i,j] ).

        Any previous ESMP_Grid, ESMP_Field, or ESMP regridding procedures 
        are destroyed.

        Arguments:
            center_lons:   2D array of longitudes, in degrees, 
                           for each of the curvilinear center points
            center_lats:   2D array of latitudes, in degrees, 
                           for each of the curvilinear center points
            center_ignore: 2D array of boolean-like values, indicating if 
                           the corresponding grid center point should be 
                           ignored in the regridding; if None, no grid 
                           center points will be ignored
            corner_lons:   2D array of longitudes, in degrees, 
                           for each of the curvilinear corner points
            corner_lats:   2D array of latitudes, in degrees, 
                           for each of the curvilinear corner points
            corner_ignore: 2D array of boolean-like values, indicating if 
                           the corresponding grid corner point should be 
                           ignored in the regridding; if None, no grid 
                           corner points will be ignored
        Returns:
            None
        Raises:
            ValueError: if the shape (dimensionality) of an argument 
                        is invalid, or if a value in an argument is invalid
            TypeError:  if an argument is not array-like
        '''
        # Make sure center_lons is an appropriate array-like argument
        center_lons_array = numpy.array(center_lons, dtype=numpy.float64, copy=False)
        if len(center_lons_array.shape) != 2:
            raise ValueError("center_lons must be two-dimensional")

        # Make sure center_lats is an appropriate array-like argument
        center_lats_array = numpy.array(center_lats, dtype=numpy.float64, copy=False)
        if len(center_lats_array.shape) != 2:
            raise ValueError("center_lats must be two-dimensional")
        if center_lats_array.shape != center_lons_array.shape:
            raise ValueError("center_lats and center_lons must have the same shape")

        if center_ignore == None:
            # Using all points, no mask created
            center_ignore_array = None
        else:
            # Make sure ignore_pts is an appropriate array-like argument
            center_ignore_array = numpy.array(center_ignore, dtype=numpy.bool, copy=False)
            if len(center_ignore_array.shape) != 2:
                raise ValueError("center_ignore must be two-dimensional")
            if center_ignore_array.shape != center_lons_array.shape:
                raise ValueError("center_ignore and center_lons must have the same shape")
            # If not actually ignoring any points, do not create a mask
            if not center_ignore_array.any():
                center_ignore_array = None

        if (corner_lons != None) and (corner_lats != None):
            # Corner points specified

            # Make sure corner_lons is an appropriate array-like argument
            corner_lons_array = numpy.array(corner_lons, dtype=numpy.float64, copy=False)
            if len(corner_lons_array.shape) != 2:
                raise ValueError("corner_lons must be two-dimensional")
            if corner_lons_array.shape != (center_lons_array.shape[0] + 1, 
                                           center_lons_array.shape[1] + 1):
                raise ValueError("corner_lons must have one more point along " \
                                 "each dimension when compared to center_lons")

            # Make sure corner_lats is an appropriate array-like argument
            corner_lats_array = numpy.array(corner_lats, dtype=numpy.float64, copy=False)
            if len(corner_lats_array.shape) != 2:
                raise ValueError("corner_lats must be two-dimensional")
            if corner_lats_array.shape != corner_lons_array.shape:
                raise ValueError("corner_lats and corner_lons must have the same shape")

            if corner_ignore == None:
                # Using all points, no mask created
                corner_ignore_array = None
            else:
                # Make sure ignore_pts is an appropriate array-like argument
                corner_ignore_array = numpy.array(corner_ignore, dtype=numpy.bool, copy=False)
                if len(corner_ignore_array.shape) != 2:
                    raise ValueError("corner_ignore must be two-dimensional")
                if corner_ignore_array.shape != corner_lons_array.shape:
                    raise ValueError("corner_ignore and corner_lons must have the same shape")
                # If not actually ignoring any points, do not create a mask
                if not corner_ignore_array.any():
                    corner_ignore_array = None
            
        elif corner_lons != None:
            raise ValueError("corner_lons given without corner_lats")
        elif corner_lats != None:
            raise ValueError("corner_lats given without corner_lons")
        elif corner_ignore != None:
            raise ValueError("corner_ignore given without corner_lons and corner_lats")
        else:
            # No corner points specified
            corner_lats_array = None
            corner_lons_array = None
            corner_ignore_array = None

        # Release any regridding procedures and clear the dictionaries
        for handle in self.__rect_to_curv_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__rect_to_curv_handles.clear()
        for handle in self.__curv_to_rect_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__curv_to_rect_handles.clear()
        # Destroy any curvilinear ESMP_Fields
        if self.__curv_src_field != None:
            ESMP.ESMP_FieldDestroy(self.__curv_src_field)
            self.__curv_src_field = None
        if self.__curv_dest_field != None:
            ESMP.ESMP_FieldDestroy(self.__curv_dest_field)
            self.__curv_dest_field = None
        # Destroy any previous curvilinear ESMP_Grid
        if self.__curv_grid != None:
            ESMP.ESMP_GridDestroy(self.__curv_grid);
            self.__curv_grid = None

        # Create the curvilinear longitude, latitude ESMP_Grid using
        # ESMP_GridCreateNoPeriDim for the typical case in Ferret.
        # ESMP_GridCreate1PeriDim assumes that the full globe is to
        # be used; that there is a center point provided for a cell
        # between the last latitude and the first latitude and 
        # thus interpolates between the last and first longitude. 
        self.__curv_shape = center_lons_array.shape
        grid_shape = numpy.array(self.__curv_shape, dtype=numpy.int32)
        self.__curv_grid = ESMP.ESMP_GridCreateNoPeriDim(grid_shape, 
                                         ESMP.ESMP_COORDSYS_SPH_DEG, 
                                         ESMP.ESMP_TYPEKIND_R8)

        if corner_lats_array != None:
            # Allocate space for the grid corner coordinates
            ESMP.ESMP_GridAddCoord(self.__curv_grid, ESMP.ESMP_STAGGERLOC_CORNER)

            # Retrieve the grid corner coordinate arrays in the ESMP_Grid
            grid_lon_coords = ESMP.ESMP_GridGetCoordPtr(self.__curv_grid, 0, 
                                                        ESMP.ESMP_STAGGERLOC_CORNER)
            grid_lat_coords = ESMP.ESMP_GridGetCoordPtr(self.__curv_grid, 1, 
                                                        ESMP.ESMP_STAGGERLOC_CORNER)

            # Assign the longitudes and latitudes of the grid corners in the ESMP_Grid
            grid_lon_coords[:] = corner_lons_array.flatten('F')
            grid_lat_coords[:] = corner_lats_array.flatten('F')

            # Add a mask if not considering all the corner points
            if corner_ignore_array != None:
                # Allocate space for the grid corners mask
                ESMP.ESMP_GridAddItem(self.__curv_grid, ESMP.ESMP_GRIDITEM_MASK, 
                                                        ESMP.ESMP_STAGGERLOC_CORNER)
                # Retrieve the grid corners mask array in the ESMP_Grid
                ignore_mask = ESMP.ESMP_GridGetItem(self.__curv_grid, 
                                                    ESMP.ESMP_GRIDITEM_MASK, 
                                                    ESMP.ESMP_STAGGERLOC_CORNER)
                # Assign the mask in the ESMP_Grid; 
                # False (turns into zero) means use the point;
                # True (turns into one) means ignore the point
                ignore_mask[:] = corner_ignore_array.flatten('F')

        # Allocate space for the grid center coordinates
        ESMP.ESMP_GridAddCoord(self.__curv_grid, ESMP.ESMP_STAGGERLOC_CENTER)

        # Retrieve the grid center coordinate arrays in the ESMP_Grid
        grid_lon_coords = ESMP.ESMP_GridGetCoordPtr(self.__curv_grid, 0, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)
        grid_lat_coords = ESMP.ESMP_GridGetCoordPtr(self.__curv_grid, 1, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)

        # Assign the longitudes and latitudes of the grid centers in the ESMP_Grid
        grid_lon_coords[:] = center_lons_array.flatten('F')
        grid_lat_coords[:] = center_lats_array.flatten('F')

        # Add a mask if not considering all the center points
        if center_ignore_array != None:
            # Allocate space for the grid centers mask
            ESMP.ESMP_GridAddItem(self.__curv_grid, ESMP.ESMP_GRIDITEM_MASK, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)
            # Retrieve the grid centers mask array in the ESMP_Grid
            ignore_mask = ESMP.ESMP_GridGetItem(self.__curv_grid, 
                                                ESMP.ESMP_GRIDITEM_MASK, 
                                                ESMP.ESMP_STAGGERLOC_CENTER)
            # Assign the mask in the ESMP_Grid; 
            # False (turns into zero) means use the point;
            # True (turns into one) means ignore the point
            ignore_mask[:] = center_ignore_array.flatten('F')


    def assignCurvField(self, data=None):
        '''
        Possibly creates, and possible assigns, an appropriate curvilinear 
        ESMP_Field located at the center points of the grid.  An ESMP_Field 
        is created if and only if it is not already present; thus allowing 
        the "weights" computed from a previous regridding to be reused.

        If data is not None, assigns the data values to the curvilinear
        source ESMP_Field, creating the ESMP_field if it does not exist.

        If data is None, only creates the curvilinear destination ESMP_Field 
        if it does not exist.

        Arguments:
            data: 2D array of data values to be assigned in an 
                  ESMP_Field for the grid center points; if None,
                  no data in any ESMP_Field is modified.
        Returns:
            None
        Raises:
            ValueError: if data is not None, and if the shape 
                        (dimensionality) of data is invalid or 
                        if a value in data is not numeric
            TypeError:  if data, if not None, is not array-like
        '''
        if data == None:

            # Create the curvilinear destination ESMP_Field if it does not exist
            if self.__curv_dest_field == None:
                self.__curv_dest_field = ESMP.ESMP_FieldCreateGrid(self.__curv_grid, 
                                                        "curv_dest_field", 
                                                        ESMP.ESMP_TYPEKIND_R8, 
                                                        ESMP.ESMP_STAGGERLOC_CENTER)

        else:

            # Make sure data is an appropriate array-like argument
            data_array = numpy.array(data, dtype=numpy.float64, copy=True)
            if len(data_array.shape) != 2:
                raise ValueError("data must be two-dimensional")
            if data_array.shape != self.__curv_shape:
                raise ValueError("data must have the same shape " \
                                 "as the center points arrays")

            # Create the curvilinear source ESMP_Field if it does not exist
            if self.__curv_src_field == None:
                self.__curv_src_field = ESMP.ESMP_FieldCreateGrid(self.__curv_grid, 
                                                       "curv_src_field", 
                                                       ESMP.ESMP_TYPEKIND_R8, 
                                                       ESMP.ESMP_STAGGERLOC_CENTER)

            # Retrieve the field data array in the ESMP_Field
            field_ptr = ESMP.ESMP_FieldGetPtr(self.__curv_src_field)

            # Assign the data to the field array in the ESMP_Field
            field_ptr[:] = data_array.flatten('F')


    def createRectGrid(self, edge_lons, edge_lats, center_ignore=None, 
                       corner_ignore=None):
        '''
        Create the rectilinear grid as an ESMP_Grid using the provided cell 
        edge longitudes and latitudes to define the grid center and corner 
        points.  Rectilinear data is assigned to the center points.  Grid
        corner point coordinates are assigned as corner_pt[i,j] = 
        ( edge_lons[i], edge_lats[j] ).  Grid center point coordinates are
        assigned as center_pt[i,j]= ( (edge_lons[i] + edge_lons[i+1]) / 2,
        (edge_lats[j] + edge_lats[j+1]) / 2 ).

        Any previous ESMP_Grid, ESMP_Field, or ESMP regridding procedures 
        are destroyed.

        Arguments:
            edge_lons:     1D array of longitudes, in degrees, 
                           for each of the rectilinear grid cells edges;
                           must be strictly increasing values
            edge_lats:     1D array of latitudes, in degrees, 
                           for each of the rectilinear grid cells edges;
                           must be strictly increasing values
            center_ignore: 2D array of boolean-like values, indicating if 
                           the corresponding grid center point should be 
                           ignored in the regridding; if None, no grid 
                           center points will be ignored
            corner_ignore: 2D array of boolean-like values, indicating if 
                           the corresponding grid corner point should be 
                           ignored in the regridding; if None, no grid 
                           corner points will be ignored
        Returns:
            None
        Raises:
            ValueError: if the shape (dimensionality) of an argument 
                        is invalid, or if a value in an argument is invalid
            TypeError:  if an argument is not array-like
        '''
        # Make sure edge_lons is an appropriate array-like argument
        lons_array = numpy.array(edge_lons, dtype=numpy.float64, copy=False)
        if len(lons_array.shape) != 1:
            raise ValueError("edge_lons must be one-dimensional")
        increasing = ( lons_array[:-1] < lons_array[1:] )
        if not increasing.all():
            raise ValueError("edge_lons must contain strictly increasing values")

        # Make sure edge_lats is an appropriate array-like argument
        lats_array = numpy.array(edge_lats, dtype=numpy.float64, copy=True)
        if len(lats_array.shape) != 1:
            raise ValueError("edge_lats must be one-dimensional")
        increasing = ( lats_array[:-1] < lats_array[1:] )
        if not increasing.all():
            raise ValueError("edge_lats must contain strictly increasing values")

        if center_ignore == None:
            # Using all center points, no mask created
            center_ignore_array = None
        else:
            # Make sure center_ignore is an appropriate array-like argument
            center_ignore_array = numpy.array(center_ignore, dtype=numpy.bool, copy=False)
            if len(center_ignore_array.shape) != 2:
                raise ValueError("center_ignore must be two-dimensional")
            if (center_ignore_array.shape[0] != lons_array.shape[0] - 1) or \
               (center_ignore_array.shape[1] != lats_array.shape[0] - 1):
                raise ValueError("center_ignore must have the shape " \
                                 "( len(edge_lons) - 1, len(edge_lats) - 1 )")
            # If not actually ignoring any center points, do not create a mask
            if not center_ignore_array.any():
                center_ignore_array = None

        if corner_ignore == None:
            # Using all corner points, no mask created
            corner_ignore_array = None
        else:
            # Make sure corner_ignore is an appropriate array-like argument
            corner_ignore_array = numpy.array(corner_ignore, dtype=numpy.bool, copy=False)
            if len(corner_ignore_array.shape) != 2:
                raise ValueError("corner_ignore must be two-dimensional")
            if (corner_ignore_array.shape[0] != lons_array.shape[0]) or \
               (corner_ignore_array.shape[1] != lats_array.shape[0]):
                raise ValueError("corner_ignore must have the shape " \
                                 "( len(edge_lons), len(edge_lats) )")
            # If not actually ignoring any points, do not create a mask
            if not corner_ignore_array.any():
                corner_ignore_array = None

        # Release any regridding procedures and clear the dictionaries
        for handle in self.__rect_to_curv_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__rect_to_curv_handles.clear()
        for handle in self.__curv_to_rect_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__curv_to_rect_handles.clear()
        # Destroy any rectilinear ESMP_Fields
        if self.__rect_src_field != None:
            ESMP.ESMP_FieldDestroy(self.__rect_src_field)
            self.__rect_src_field = None
        if self.__rect_dest_field != None:
            ESMP.ESMP_FieldDestroy(self.__rect_dest_field)
            self.__rect_dest_field = None
        # Destroy any previous rectilinear ESMP_Grid
        if self.__rect_grid != None:
            ESMP.ESMP_GridDestroy(self.__rect_grid);
            self.__rect_grid = None

        # Create the rectilinear longitude, latitude grid using
        # ESMP_GridCreateNoPeriDim for the typical case in Ferret.
        # ESMP_GridCreate1PeriDim assumes that the full globe is to
        # be used; that there is a center point provided for a cell
        # between the last latitude and the first latitude and 
        # thus interpolates between the last and first longitude. 
        self.__rect_shape = (lons_array.shape[0] - 1, lats_array.shape[0] - 1)
        grid_shape = numpy.array(self.__rect_shape, dtype=numpy.int32)
        if self.__rect_grid != None:
            ESMP.ESMP_GridDestroy(self.__rect_grid)
        self.__rect_grid = ESMP.ESMP_GridCreateNoPeriDim(grid_shape, 
                                         ESMP.ESMP_COORDSYS_SPH_DEG, 
                                         ESMP.ESMP_TYPEKIND_R8)

        # Allocate space for the grid corner coordinates
        ESMP.ESMP_GridAddCoord(self.__rect_grid, ESMP.ESMP_STAGGERLOC_CORNER)

        # Retrieve the grid corner coordinate arrays in the ESMP_Grid
        grid_lon_coords = ESMP.ESMP_GridGetCoordPtr(self.__rect_grid, 0, 
                                                    ESMP.ESMP_STAGGERLOC_CORNER)
        grid_lat_coords = ESMP.ESMP_GridGetCoordPtr(self.__rect_grid, 1, 
                                                    ESMP.ESMP_STAGGERLOC_CORNER)

        # Assign the longitudes and latitudes of the grid corners in the ESMP_Grid
        # numpy.tile([a,b,c], 2) = [a,b,c,a,b,c]
        grid_lon_coords[:] = numpy.tile(lons_array, lats_array.shape[0])
        # numpy.repeat([a,b,c], 2) = [a,a,b,b,c,c]
        grid_lat_coords[:] = numpy.repeat(lats_array, lons_array.shape[0])

        # Add a mask if not considering all the corner points
        if ( corner_ignore_array != None ):
            # Allocate space for the grid corners mask
            ESMP.ESMP_GridAddItem(self.__rect_grid, ESMP.ESMP_GRIDITEM_MASK, 
                                                    ESMP.ESMP_STAGGERLOC_CORNER)
            # Retrieve the grid corners mask array in the ESMP_Grid
            ignore_mask = ESMP.ESMP_GridGetItem(self.__rect_grid, 
                                                ESMP.ESMP_GRIDITEM_MASK, 
                                                ESMP.ESMP_STAGGERLOC_CORNER)
            # Assign the mask in the ESMP_Grid; 
            # False (turns into zero) means use the point;
            # True (turns into one) means ignore the point;
            # flatten in column-major (F) order to match lon-lat assignment order
            ignore_mask[:] = corner_ignore_array.flatten('F')

        # Allocate space for the grid center coordinates
        ESMP.ESMP_GridAddCoord(self.__rect_grid, ESMP.ESMP_STAGGERLOC_CENTER)

        # Retrieve the grid corner coordinate arrays in the ESMP_Grid
        grid_lon_coords = ESMP.ESMP_GridGetCoordPtr(self.__rect_grid, 0, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)
        grid_lat_coords = ESMP.ESMP_GridGetCoordPtr(self.__rect_grid, 1, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)

        # Assign the longitudes and latitudes of the grid centers in the ESMP_Grid
        mid_lons = 0.5 * (lons_array[:-1] + lons_array[1:])
        mid_lats = 0.5 * (lats_array[:-1] + lats_array[1:])
        # numpy.tile([a,b,c], 2) = [a,b,c,a,b,c]
        grid_lon_coords[:] = numpy.tile(mid_lons, mid_lats.shape[0])
        # numpy.repeat([a,b,c], 2) = [a,a,b,b,c,c]
        grid_lat_coords[:] = numpy.repeat(mid_lats, mid_lons.shape[0])

        # Add a mask if not considering all the center points
        if ( center_ignore_array != None ):
            # Allocate space for the grid centers mask
            ESMP.ESMP_GridAddItem(self.__rect_grid, ESMP.ESMP_GRIDITEM_MASK, 
                                                    ESMP.ESMP_STAGGERLOC_CENTER)
            # Retrieve the grid centers mask array in the ESMP_Grid
            ignore_mask = ESMP.ESMP_GridGetItem(self.__rect_grid, 
                                                ESMP.ESMP_GRIDITEM_MASK, 
                                                ESMP.ESMP_STAGGERLOC_CENTER)
            # Assign the mask in the ESMP_Grid; 
            # False (turns into zero) means use the point;
            # True (turns into one) means ignore the point;
            # flatten in column-major (F) order to match lon-lat assignment order
            ignore_mask[:] = center_ignore_array.flatten('F')


    def assignRectField(self, data=None):
        '''
        Possibly creates, and possible assigns, an appropriate rectilinear 
        ESMP_Field located at the center points of the grid.  An ESMP_Field 
        is created if and only if it is not already present; thus allowing 
        the "weights" computed from a previous regridding to be reused.

        If data is not None, assigns the data values to the rectilinear
        source ESMP_Field, creating the ESMP_field if it does not exist.

        If data is None, only creates the rectilinear destination ESMP_Field 
        if it does not exist.

        Arguments:
            data: 2D array of data values to be assigned in an 
                  ESMP_Field for the grid center points; if None,
                  no data in any ESMP_Field is modified.
        Returns:
            None
        Raises:
            ValueError: if data is not None, and if the shape 
                        (dimensionality) of data is invalid or 
                        if a value in data is not numeric
            TypeError:  if data, if not None, is not array-like
        '''
        if data == None:

            # Create the rectilinear destination ESMP_Field if it does not exist
            if self.__rect_dest_field == None:
                self.__rect_dest_field = ESMP.ESMP_FieldCreateGrid(self.__rect_grid, 
                                                        "rect_dest_field", 
                                                        ESMP.ESMP_TYPEKIND_R8, 
                                                        ESMP.ESMP_STAGGERLOC_CENTER)

        else:

            # Make sure data is an appropriate array-like argument
            data_array = numpy.array(data, dtype=numpy.float64, copy=True)
            if len(data_array.shape) != 2:
                raise ValueError("data must be two-dimensional")
            if data_array.shape != self.__rect_shape:
                raise ValueError("data must have the same shape " \
                                 "as the center points arrays")

            # Create the rectilinear source ESMP_Field if it does not exist
            if self.__rect_src_field == None:
                self.__rect_src_field = ESMP.ESMP_FieldCreateGrid(self.__rect_grid, 
                                                       "rect_src_field", 
                                                       ESMP.ESMP_TYPEKIND_R8, 
                                                       ESMP.ESMP_STAGGERLOC_CENTER)

            # Retrieve the field data array in the ESMP_Field
            field_ptr = ESMP.ESMP_FieldGetPtr(self.__rect_src_field)

            # Assign the data to the field array in the ESMP_Field
            field_ptr[:] = data_array.flatten('F')


    def regridCurvToRect(self, undef_val, 
                         method=ESMP.ESMP_REGRIDMETHOD_BILINEAR):
        '''
        Regrids from the curvilinear source ESMP_Field to the rectilinear
        destination ESMP_Field using the given regridding method.  Reuses 
        the appropriate regridding procedure if one already exists; 
        otherwise a new regridding procedure is created and stored.

        Prior to calling this method, the curvilinear source ESMP_Field 
        must be created by calling createCurvGrid, then assignCurvField 
        with valid data.  The rectilinear destination ESMP_Field must
        also have been created by calling createRectGrid, and then 
        assignRectField with no data argument (or None for data).

        Arguments:
            undef_val: numpy array containing one numeric value to 
                       be used as the undefined data value in the 
                       returned array
            method:    one of the ESMP regridding method identifiers, 
                       such as:
                           ESMP.ESMP_REGRIDMETHOD_BILINEAR
                           ESMP.ESMP_REGRIDMETHOD_CONSERVE
                           ESMP.ESMP_REGRIDMETHOD_PATCH
                       Conservative regridding requires that both 
                       corner and center point coordinates are 
                       defined in the grids. 
        Returns:
            data: a 2D array of data values located at the rectilinear
                  grid centers representing the regridded curvilinear
                  ESMP_Field data.  The undefined data value will be
                  assigned to unassigned data points.
        Raises:
            ValueError: if either the curvilinear source ESMP_Field or
                        the rectilinear destination ESMP_Field does not
                        exist.
        '''
        # Check that the source and destination fields exist
        if self.__curv_src_field == None:
            raise ValueError("Curvilinear source ESMP_Field does not exist")
        if self.__rect_dest_field == None:
            raise ValueError("Rectilinear destination ESMP_Field does not exist")
        # Check if a regrid procedure handle already exists for this method
        handle = self.__curv_to_rect_handles.get(method, None)
        # If no handle found, create one
        if handle == None:
            # Assign the value in the masks marking points to be ignored
            ignore_mask_value = numpy.array([1], dtype=numpy.int32)
            # Generate the procedure handle
            handle = ESMP.ESMP_FieldRegridStore(self.__curv_src_field, 
                                                self.__rect_dest_field, 
                                                ignore_mask_value, ignore_mask_value, 
                                                method, ESMP.ESMP_UNMAPPEDACTION_IGNORE)
            # Save the handle for this method for future regrids
            self.__curv_to_rect_handles[method] = handle
        # Initialize the destination field values with the undefined data value
        field_ptr = ESMP.ESMP_FieldGetPtr(self.__rect_dest_field)
        field_ptr[:] = undef_val
        # Perform the regridding, zeroing out only the 
        # destination fields values that will be assigned
        ESMP.ESMP_FieldRegrid(self.__curv_src_field, self.__rect_dest_field, 
                              handle, ESMP.ESMP_REGION_SELECT)
        # Make a copy of the destination field values to return, reshaped to 2D
        result = numpy.array(field_ptr, dtype=numpy.float64, copy=True)
        result = result.reshape(self.__rect_shape, order = 'F')

        return result


    def regridRectToCurv(self, undef_val, 
                         method=ESMP.ESMP_REGRIDMETHOD_BILINEAR):
        '''
        Regrids from the rectilinear source ESMP_Field to the curvilinear
        destination ESMP_Field using the given regridding method.  Reuses 
        the appropriate regridding procedure if one already exists; 
        otherwise a new regridding procedure is created and stored.

        Prior to calling this method, the rectilinear source ESMP_Field 
        must be created by calling createRectGrid, then assignRectField 
        with valid data.  The curvilinear destination ESMP_Field must
        also have been created by calling createCurvGrid, and then 
        assignCurvField with no data argument (or None for data).

        Arguments:
            undef_val: numpy array containing one numeric value to 
                       be used as the undefined data value in the 
                       returned array
            method:    one of the ESMP regridding method identifiers, 
                       such as:
                           ESMP.ESMP_REGRIDMETHOD_BILINEAR
                           ESMP.ESMP_REGRIDMETHOD_CONSERVE
                           ESMP.ESMP_REGRIDMETHOD_PATCH
                       Conservative regridding requires that both 
                       corner and center point coordinates are 
                       defined in the grids. 
        Returns:
            data: a 2D array of data values located at the curvilinear
                  grid centers representing the regridded rectilinear
                  ESMP_Field data.  The undefined data value will be
                  assigned to unassigned data points.
        Raises:
            ValueError: if either the rectilinear source ESMP_Field or
                        the curvilinear destination ESMP_Field does not
                        exist.
        '''
        # Check that the source and destination fields exist
        if self.__rect_src_field == None:
            raise ValueError("Rectilinear source ESMP_Field does not exist")
        if self.__curv_dest_field == None:
            raise ValueError("Curvilinear destination ESMP_Field does not exist")
        # Check if a regrid procedure handle already exists for this method
        handle = self.__rect_to_curv_handles.get(method, None)
        # If no handle found, create one
        if handle == None:
            # Assign the value in the masks marking points to be ignored
            ignore_mask_value = numpy.array([1], dtype=numpy.int32)
            # Generate the procedure handle
            handle = ESMP.ESMP_FieldRegridStore(self.__rect_src_field, 
                                                self.__curv_dest_field, 
                                                ignore_mask_value, ignore_mask_value, 
                                                method, ESMP.ESMP_UNMAPPEDACTION_IGNORE)
            # Save the handle for this method for future regrids
            self.__rect_to_curv_handles[method] = handle
        # Initialize the destination field values with the undefined data value
        field_ptr = ESMP.ESMP_FieldGetPtr(self.__curv_dest_field)
        field_ptr[:] = undef_val
        # Perform the regridding, zeroing out only the 
        # destination fields values that will be assigned
        ESMP.ESMP_FieldRegrid(self.__rect_src_field, self.__curv_dest_field, 
                              handle, ESMP.ESMP_REGION_SELECT)
        # Make a copy of the destination field values to return, reshaped to 2D
        result = numpy.array(field_ptr, dtype=numpy.float64, copy=True)
        result = result.reshape(self.__curv_shape, order = 'F')

        return result


    def finalize(self):
        '''
        Destroys any ESMP_Grid, ESMP_Field, and ESMP regridding 
        procedures present in this instance.  If ESMP is no longer 
        needed, ESMP.ESMP_Finalize() should be called to free any 
        ESMP and ESMF resources.

        Arguments:
            None
        Returns:
            None
        '''
        # Release any regridding procedures and clear the dictionaries
        for handle in self.__rect_to_curv_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__rect_to_curv_handles.clear()
        for handle in self.__curv_to_rect_handles.values():
            ESMP.ESMP_FieldRegridRelease(handle)
        self.__curv_to_rect_handles.clear()
        # Destroy any ESMP_Fields
        if self.__rect_src_field != None:
            ESMP.ESMP_FieldDestroy(self.__rect_src_field)
            self.__rect_src_field = None
        if self.__rect_dest_field != None:
            ESMP.ESMP_FieldDestroy(self.__rect_dest_field)
            self.__rect_dest_field = None
        if self.__curv_src_field != None:
            ESMP.ESMP_FieldDestroy(self.__curv_src_field)
            self.__curv_src_field = None
        if self.__curv_dest_field != None:
            ESMP.ESMP_FieldDestroy(self.__curv_dest_field)
            self.__curv_dest_field = None
        # Destroy any ESMP_Grids
        if self.__rect_grid != None:
            ESMP.ESMP_GridDestroy(self.__rect_grid);
            self.__rect_grid = None
        if self.__curv_grid != None:
            ESMP.ESMP_GridDestroy(self.__curv_grid);
            self.__curv_grid = None
        # clear the shape attributes just to be complete
        self.__rect_shape = None
        self.__curv_shape = None


###
### The following is for testing "by-hand" and to serve as a usage example
###


def __createExampleCurvData():
    '''
    Creates and returns example longitude, latitudes, and data for a curvilinear 
    grid.  Uses the GFDL tripolar grid.  Assigns grid center point data[i,j] 
        = cos(lon[i,j]) * cos(3.6 * (lat[i,j] - 65.0)) for areas over ocean, 
        = 1.0E20 for areas over land.

    Arguments:
        None
    Returns:
        (corner_lons, corner_lats, center_lons, center_lats, data) where:
        corner_lons: numpy.float64 2D array of curvilinear corner point longitude coordinates
        corner_lats: numpy.float64 2D array of curvilinear corner point latitude coordinates
        center_lons: numpy.float64 2D array of curvilinear center point longitude coordinates
        center_lats: numpy.float64 2D array of curvilinear center point latitude coordinates
        data:        numpy.float64 2D array of curvilinear center point data values
    '''
    # longitude centerpoints for the GFDL tripolar grid in the region 20W:20E, 65N:85N
    corner_lons = numpy.array( (
        ( -20.500, -19.500, -18.500, -17.500, -16.500, -15.500, -14.500, -13.500, -12.500, -11.500,
          -10.500,  -9.500,  -8.500,  -7.500,  -6.500,  -5.500,  -4.500,  -3.500,  -2.500,  -1.500,
           -0.500,   0.500,   1.500,   2.500,   3.500,   4.500,   5.500,   6.500,   7.500,   8.500,
            9.500,  10.500,  11.500,  12.500,  13.500,  14.500,  15.500,  16.500,  17.500,  18.500,
           19.500,  20.500, ),
        ( -20.502, -19.502, -18.502, -17.502, -16.501, -15.501, -14.501, -13.501, -12.501, -11.500,
          -10.500,  -9.500,  -8.500,  -7.499,  -6.499,  -5.499,  -4.499,  -3.499,  -2.498,  -1.498,
           -0.498,   0.502,   1.502,   2.503,   3.503,   4.503,   5.503,   6.503,   7.504,   8.504,
            9.504,  10.504,  11.504,  12.504,  13.505,  14.505,  15.505,  16.505,  17.505,  18.505,
           19.505,  20.505, ),
        ( -20.521, -19.519, -18.517, -17.515, -16.513, -15.511, -14.509, -13.507, -12.505, -11.503,
          -10.501,  -9.499,  -8.497,  -7.495,  -6.493,  -5.491,  -4.489,  -3.487,  -2.485,  -1.483,
           -0.481,   0.521,   1.523,   2.525,   3.526,   4.528,   5.530,   6.532,   7.533,   8.535,
            9.537,  10.538,  11.540,  12.541,  13.543,  14.544,  15.545,  16.547,  17.548,  18.549,
           19.550,  20.551, ),
        ( -20.560, -19.555, -18.549, -17.544, -16.538, -15.532, -14.526, -13.521, -12.515, -11.509,
          -10.503,  -9.497,  -8.491,  -7.485,  -6.479,  -5.474,  -4.468,  -3.462,  -2.456,  -1.451,
           -0.445,   0.560,   1.566,   2.571,   3.577,   4.582,   5.587,   6.592,   7.597,   8.601,
            9.606,  10.611,  11.615,  12.619,  13.623,  14.627,  15.631,  16.634,  17.638,  18.641,
           19.644,  20.647, ),
        ( -20.624, -19.612, -18.601, -17.589, -16.578, -15.566, -14.554, -13.542, -12.530, -11.518,
          -10.506,  -9.494,  -8.482,  -7.470,  -6.458,  -5.446,  -4.434,  -3.422,  -2.411,  -1.399,
           -0.388,   0.624,   1.635,   2.646,   3.657,   4.667,   5.678,   6.688,   7.698,   8.707,
            9.717,  10.726,  11.735,  12.744,  13.752,  14.760,  15.768,  16.775,  17.782,  18.789,
           19.795,  20.801, ),
        ( -20.714, -19.694, -18.674, -17.654, -16.634, -15.614, -14.593, -13.573, -12.552, -11.531,
          -10.510,  -9.490,  -8.469,  -7.448,  -6.427,  -5.407,  -4.386,  -3.366,  -2.346,  -1.326,
           -0.306,   0.714,   1.733,   2.752,   3.771,   4.789,   5.807,   6.824,   7.842,   8.858,
            9.875,  10.890,  11.906,  12.921,  13.935,  14.949,  15.962,  16.975,  17.987,  18.998,
           20.009,  21.019, ),
        ( -20.835, -19.804, -18.773, -17.742, -16.710, -15.678, -14.646, -13.614, -12.581, -11.549,
          -10.516,  -9.484,  -8.451,  -7.419,  -6.386,  -5.354,  -4.322,  -3.290,  -2.258,  -1.227,
           -0.196,   0.835,   1.865,   2.894,   3.924,   4.952,   5.980,   7.008,   8.035,   9.061,
           10.086,  11.111,  12.135,  13.158,  14.180,  15.202,  16.222,  17.242,  18.260,  19.278,
           20.295,  21.311, ),
        ( -20.991, -19.946, -18.901, -17.855, -16.809, -15.762, -14.715, -13.667, -12.620, -11.572,
          -10.524,  -9.476,  -8.428,  -7.380,  -6.333,  -5.285,  -4.238,  -3.191,  -2.145,  -1.099,
           -0.054,   0.991,   2.036,   3.079,   4.122,   5.164,   6.205,   7.245,   8.284,   9.322,
           10.360,  11.396,  12.430,  13.464,  14.497,  15.528,  16.558,  17.586,  18.613,  19.639,
           20.663,  21.686, ),
        ( -21.190, -20.127, -19.063, -17.999, -16.933, -15.868, -14.802, -13.735, -12.668, -11.601,
          -10.534,  -9.466,  -8.399,  -7.332,  -6.265,  -5.198,  -4.132,  -3.067,  -2.001,  -0.937,
            0.127,   1.190,   2.251,   3.312,   4.372,   5.431,   6.488,   7.545,   8.599,   9.653,
           10.704,  11.755,  12.803,  13.850,  14.895,  15.939,  16.980,  18.019,  19.057,  20.093,
           21.126,  22.158, ),
        ( -21.437, -20.351, -19.265, -18.177, -17.089, -16.000, -14.910, -13.819, -12.728, -11.637,
          -10.546,  -9.454,  -8.363,  -7.272,  -6.181,  -5.090,  -4.000,  -2.911,  -1.823,  -0.735,
            0.351,   1.437,   2.521,   3.603,   4.684,   5.764,   6.841,   7.917,   8.991,  10.063,
           11.133,  12.200,  13.266,  14.329,  15.389,  16.447,  17.503,  18.555,  19.605,  20.653,
           21.697,  22.739, ),
        ( -21.741, -20.629, -19.514, -18.398, -17.281, -16.163, -15.044, -13.924, -12.803, -11.682,
          -10.561,  -9.439,  -8.318,  -7.197,  -6.076,  -4.956,  -3.837,  -2.719,  -1.602,  -0.486,
            0.629,   1.741,   2.852,   3.962,   5.069,   6.173,   7.276,   8.376,   9.473,  10.567,
           11.659,  12.748,  13.833,  14.915,  15.994,  17.070,  18.142,  19.211,  20.276,  21.337,
           22.394,  23.448, ),
        ( -22.116, -20.969, -19.821, -18.670, -17.518, -16.364, -15.208, -14.052, -12.895, -11.737,
          -10.579,  -9.421,  -8.263,  -7.105,  -5.948,  -4.792,  -3.636,  -2.482,  -1.330,  -0.179,
            0.969,   2.116,   3.260,   4.401,   5.540,   6.675,   7.808,   8.937,  10.062,  11.184,
           12.301,  13.415,  14.525,  15.630,  16.731,  17.827,  18.919,  20.006,  21.088,  22.165,
           23.237,  24.304, ),
        ( -22.574, -21.387, -20.196, -19.003, -17.808, -16.610, -15.411, -14.210, -13.008, -11.805,
          -10.602,  -9.398,  -8.195,  -6.992,  -5.790,  -4.589,  -3.390,  -2.192,  -0.997,   0.196,
            1.387,   2.574,   3.758,   4.939,   6.116,   7.288,   8.457,   9.621,  10.780,  11.934,
           13.083,  14.226,  15.364,  16.496,  17.623,  18.743,  19.857,  20.965,  22.067,  23.162,
           24.251,  25.333, ),
        ( -23.136, -21.899, -20.657, -19.412, -18.164, -16.913, -15.659, -14.404, -13.147, -11.888,
          -10.630,  -9.370,  -8.112,  -6.853,  -5.596,  -4.341,  -3.087,  -1.836,  -0.588,   0.657,
            1.899,   3.136,   4.369,   5.597,   6.820,   8.037,   9.249,  10.454,  11.653,  12.846,
           14.031,  15.210,  16.381,  17.544,  18.700,  19.848,  20.988,  22.120,  23.244,  24.359,
           25.466,  26.564, ),
        ( -23.827, -22.529, -21.225, -19.917, -18.604, -17.287, -15.966, -14.643, -13.318, -11.992,
          -10.664,  -9.336,  -8.008,  -6.682,  -5.357,  -4.034,  -2.713,  -1.396,  -0.083,   1.225,
            2.529,   3.827,   5.119,   6.404,   7.683,   8.954,  10.217,  11.472,  12.719,  13.956,
           15.185,  16.404,  17.613,  18.813,  20.002,  21.181,  22.350,  23.508,  24.655,  25.792,
           26.918,  28.033, ),
        ( -24.681, -23.309, -21.929, -20.542, -19.149, -17.751, -16.348, -14.941, -13.532, -12.120,
          -10.707,  -9.293,  -7.880,  -6.468,  -5.059,  -3.652,  -2.249,  -0.851,   0.542,   1.929,
            3.309,   4.681,   6.045,   7.400,   8.746,  10.081,  11.406,  12.720,  14.023,  15.313,
           16.591,  17.857,  19.110,  20.350,  21.577,  22.790,  23.990,  25.176,  26.348,  27.507,
           28.652,  29.783, ),
        ( -25.747, -24.284, -22.810, -21.326, -19.834, -18.334, -16.828, -15.316, -13.800, -12.281,
          -10.761,  -9.239,  -7.719,  -6.200,  -4.684,  -3.172,  -1.666,  -0.166,   1.326,   2.810,
            4.284,   5.747,   7.199,   8.639,  10.065,  11.478,  12.876,  14.259,  15.627,  16.979,
           18.314,  19.633,  20.934,  22.219,  23.486,  24.735,  25.967,  27.182,  28.379,  29.559,
           30.721,  31.866, ),
        ( -27.094, -25.518, -23.927, -22.322, -20.705, -19.077, -17.440, -15.795, -14.143, -12.488,
          -10.830,  -9.170,  -7.512,  -5.857,  -4.205,  -2.560,  -0.923,   0.705,   2.322,   3.927,
            5.518,   7.094,   8.653,  10.196,  11.720,  13.224,  14.709,  16.174,  17.617,  19.038,
           20.437,  21.814,  23.168,  24.500,  25.809,  27.095,  28.359,  29.600,  30.819,  32.015,
           33.190,  34.344, ),
        ( -28.821, -27.106, -25.368, -23.610, -21.834, -20.042, -18.235, -16.418, -14.591, -12.757,
          -10.919,  -9.081,  -7.243,  -5.409,  -3.582,  -1.765,   0.042,   1.834,   3.610,   5.368,
            7.106,   8.821,  10.514,  12.181,  13.822,  15.436,  17.022,  18.579,  20.107,  21.605,
           23.074,  24.512,  25.920,  27.298,  28.647,  29.966,  31.256,  32.518,  33.751,  34.957,
           36.136,  37.289, ),
        ( -31.083, -29.193, -27.269, -25.315, -23.333, -21.326, -19.298, -17.251, -15.189, -13.118,
          -11.040,  -8.960,  -6.882,  -4.811,  -2.749,  -0.702,   1.326,   3.333,   5.315,   7.269,
            9.193,  11.083,  12.939,  14.757,  16.538,  18.279,  19.980,  21.640,  23.260,  24.838,
           26.376,  27.874,  29.331,  30.749,  32.129,  33.470,  34.775,  36.044,  37.278,  38.478,
           39.646,  40.781, ),
        ( -34.122, -32.014, -29.854, -27.645, -25.391, -23.096, -20.766, -18.406, -16.022, -13.620,
          -11.208,  -8.792,  -6.380,  -3.978,  -1.594,   0.766,   3.096,   5.391,   7.645,   9.854,
           12.014,  14.122,  16.176,  18.175,  20.115,  21.998,  23.823,  25.590,  27.299,  28.952,
           30.549,  32.092,  33.583,  35.022,  36.412,  37.754,  39.050,  40.302,  41.512,  42.681,
           43.812,  44.906, ),
        ( -38.339, -35.964, -33.503, -30.961, -28.342, -25.652, -22.899, -20.092, -17.240, -14.357,
          -11.455,  -8.545,  -5.643,  -2.760,   0.092,   2.899,   5.652,   8.342,  10.961,  13.503,
           15.964,  18.339,  20.626,  22.826,  24.938,  26.963,  28.903,  30.759,  32.536,  34.234,
           35.859,  37.412,  38.898,  40.319,  41.679,  42.980,  44.227,  45.423,  46.569,  47.669,
           48.725,  49.740, ),
      ), dtype = numpy.float64)
    # latitude centerpoints for the GFDL tripolar grid in the region 20W:20E, 65N:85N
    corner_lats = numpy.array( (
        ( 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500,
          64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500,
          64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500,
          64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500, 64.500,
          64.500, 64.500, ),
        ( 65.492, 65.493, 65.495, 65.496, 65.497, 65.498, 65.498, 65.499, 65.500, 65.500,
          65.500, 65.500, 65.500, 65.500, 65.499, 65.498, 65.498, 65.497, 65.496, 65.495,
          65.493, 65.492, 65.490, 65.488, 65.486, 65.484, 65.482, 65.480, 65.477, 65.474,
          65.472, 65.469, 65.466, 65.462, 65.459, 65.455, 65.452, 65.448, 65.444, 65.440,
          65.436, 65.431, ),
        ( 66.476, 66.480, 66.484, 66.488, 66.491, 66.493, 66.495, 66.497, 66.499, 66.499,
          66.500, 66.500, 66.499, 66.499, 66.497, 66.495, 66.493, 66.491, 66.488, 66.484,
          66.480, 66.476, 66.471, 66.465, 66.460, 66.453, 66.447, 66.440, 66.432, 66.424,
          66.416, 66.407, 66.398, 66.389, 66.379, 66.368, 66.357, 66.346, 66.334, 66.322,
          66.310, 66.297, ),
        ( 67.460, 67.467, 67.474, 67.479, 67.485, 67.489, 67.493, 67.496, 67.498, 67.499,
          67.500, 67.500, 67.499, 67.498, 67.496, 67.493, 67.489, 67.485, 67.479, 67.474,
          67.467, 67.460, 67.452, 67.443, 67.434, 67.424, 67.413, 67.401, 67.389, 67.376,
          67.362, 67.348, 67.333, 67.317, 67.301, 67.283, 67.266, 67.247, 67.228, 67.208,
          67.188, 67.167, ),
        ( 68.445, 68.455, 68.464, 68.472, 68.479, 68.485, 68.490, 68.494, 68.497, 68.499,
          68.500, 68.500, 68.499, 68.497, 68.494, 68.490, 68.485, 68.479, 68.472, 68.464,
          68.455, 68.445, 68.434, 68.421, 68.408, 68.394, 68.379, 68.364, 68.347, 68.329,
          68.310, 68.290, 68.269, 68.247, 68.225, 68.201, 68.176, 68.151, 68.124, 68.097,
          68.068, 68.039, ),
        ( 69.430, 69.442, 69.454, 69.464, 69.473, 69.481, 69.487, 69.492, 69.496, 69.499,
          69.500, 69.500, 69.499, 69.496, 69.492, 69.487, 69.481, 69.473, 69.464, 69.454,
          69.442, 69.430, 69.416, 69.400, 69.384, 69.366, 69.347, 69.327, 69.305, 69.282,
          69.258, 69.233, 69.206, 69.179, 69.150, 69.120, 69.088, 69.056, 69.022, 68.987,
          68.951, 68.914, ),
        ( 70.415, 70.430, 70.444, 70.456, 70.467, 70.477, 70.484, 70.491, 70.495, 70.498,
          70.500, 70.500, 70.498, 70.495, 70.491, 70.484, 70.477, 70.467, 70.456, 70.444,
          70.430, 70.415, 70.398, 70.379, 70.359, 70.338, 70.315, 70.290, 70.264, 70.236,
          70.207, 70.177, 70.145, 70.111, 70.076, 70.039, 70.002, 69.962, 69.921, 69.879,
          69.835, 69.790, ),
        ( 71.400, 71.418, 71.434, 71.449, 71.462, 71.473, 71.482, 71.489, 71.494, 71.498,
          71.500, 71.500, 71.498, 71.494, 71.489, 71.482, 71.473, 71.462, 71.449, 71.434,
          71.418, 71.400, 71.380, 71.358, 71.335, 71.310, 71.282, 71.254, 71.223, 71.191,
          71.156, 71.121, 71.083, 71.044, 71.002, 70.960, 70.915, 70.869, 70.821, 70.771,
          70.720, 70.667, ),
        ( 72.385, 72.406, 72.425, 72.441, 72.456, 72.468, 72.479, 72.487, 72.493, 72.498,
          72.500, 72.500, 72.498, 72.493, 72.487, 72.479, 72.468, 72.456, 72.441, 72.425,
          72.406, 72.385, 72.362, 72.337, 72.310, 72.281, 72.250, 72.217, 72.182, 72.145,
          72.105, 72.064, 72.021, 71.976, 71.928, 71.879, 71.828, 71.775, 71.720, 71.663,
          71.604, 71.543, ),
        ( 73.370, 73.393, 73.415, 73.434, 73.450, 73.464, 73.476, 73.486, 73.493, 73.497,
          73.500, 73.500, 73.497, 73.493, 73.486, 73.476, 73.464, 73.450, 73.434, 73.415,
          73.393, 73.370, 73.344, 73.316, 73.285, 73.252, 73.217, 73.179, 73.140, 73.098,
          73.053, 73.007, 72.958, 72.907, 72.853, 72.798, 72.740, 72.680, 72.618, 72.553,
          72.487, 72.418, ),
        ( 74.354, 74.380, 74.404, 74.425, 74.444, 74.460, 74.473, 74.484, 74.492, 74.497,
          74.500, 74.500, 74.497, 74.492, 74.484, 74.473, 74.460, 74.444, 74.425, 74.404,
          74.380, 74.354, 74.325, 74.293, 74.259, 74.222, 74.183, 74.141, 74.096, 74.049,
          74.000, 73.947, 73.893, 73.835, 73.776, 73.714, 73.649, 73.582, 73.512, 73.441,
          73.366, 73.290, ),
        ( 75.337, 75.367, 75.393, 75.417, 75.438, 75.455, 75.470, 75.482, 75.491, 75.497,
          75.500, 75.500, 75.497, 75.491, 75.482, 75.470, 75.455, 75.438, 75.417, 75.393,
          75.367, 75.337, 75.305, 75.270, 75.232, 75.191, 75.147, 75.100, 75.051, 74.998,
          74.943, 74.885, 74.825, 74.761, 74.695, 74.626, 74.554, 74.480, 74.403, 74.323,
          74.241, 74.156, ),
        ( 76.320, 76.352, 76.382, 76.408, 76.431, 76.450, 76.467, 76.480, 76.490, 76.496,
          76.500, 76.500, 76.496, 76.490, 76.480, 76.467, 76.450, 76.431, 76.408, 76.382,
          76.352, 76.320, 76.284, 76.245, 76.203, 76.157, 76.109, 76.057, 76.002, 75.944,
          75.883, 75.819, 75.752, 75.682, 75.609, 75.533, 75.454, 75.372, 75.288, 75.200,
          75.109, 75.016, ),
        ( 77.300, 77.336, 77.369, 77.398, 77.423, 77.445, 77.463, 77.478, 77.489, 77.496,
          77.500, 77.500, 77.496, 77.489, 77.478, 77.463, 77.445, 77.423, 77.398, 77.369,
          77.336, 77.300, 77.261, 77.218, 77.171, 77.121, 77.067, 77.010, 76.950, 76.886,
          76.819, 76.748, 76.674, 76.597, 76.517, 76.433, 76.347, 76.257, 76.164, 76.068,
          75.968, 75.866, ),
        ( 78.279, 78.319, 78.355, 78.387, 78.415, 78.439, 78.459, 78.475, 78.487, 78.495,
          78.499, 78.499, 78.495, 78.487, 78.475, 78.459, 78.439, 78.415, 78.387, 78.355,
          78.319, 78.279, 78.235, 78.187, 78.136, 78.080, 78.021, 77.958, 77.892, 77.821,
          77.747, 77.670, 77.589, 77.504, 77.416, 77.324, 77.229, 77.131, 77.029, 76.924,
          76.816, 76.704, ),
        ( 79.254, 79.299, 79.339, 79.374, 79.405, 79.432, 79.455, 79.473, 79.486, 79.495,
          79.499, 79.499, 79.495, 79.486, 79.473, 79.455, 79.432, 79.405, 79.374, 79.339,
          79.299, 79.254, 79.206, 79.153, 79.096, 79.035, 78.969, 78.900, 78.826, 78.749,
          78.667, 78.582, 78.493, 78.400, 78.303, 78.203, 78.099, 77.991, 77.880, 77.766,
          77.648, 77.526, ),
        ( 80.226, 80.275, 80.320, 80.359, 80.394, 80.424, 80.449, 80.469, 80.484, 80.494,
          80.499, 80.499, 80.494, 80.484, 80.469, 80.449, 80.424, 80.394, 80.359, 80.320,
          80.275, 80.226, 80.172, 80.113, 80.050, 79.982, 79.909, 79.832, 79.751, 79.666,
          79.576, 79.482, 79.384, 79.282, 79.175, 79.066, 78.952, 78.834, 78.713, 78.588,
          78.459, 78.327, ),
        ( 81.192, 81.247, 81.297, 81.342, 81.381, 81.415, 81.443, 81.465, 81.482, 81.494,
          81.499, 81.499, 81.494, 81.482, 81.465, 81.443, 81.415, 81.381, 81.342, 81.297,
          81.247, 81.192, 81.131, 81.066, 80.995, 80.919, 80.838, 80.753, 80.663, 80.568,
          80.469, 80.365, 80.257, 80.144, 80.028, 79.907, 79.782, 79.654, 79.521, 79.385,
          79.245, 79.102, ),
        ( 82.150, 82.213, 82.269, 82.320, 82.364, 82.403, 82.435, 82.460, 82.480, 82.493,
          82.499, 82.499, 82.493, 82.480, 82.460, 82.435, 82.403, 82.364, 82.320, 82.269,
          82.213, 82.150, 82.082, 82.008, 81.928, 81.843, 81.753, 81.657, 81.556, 81.451,
          81.341, 81.226, 81.106, 80.982, 80.854, 80.721, 80.584, 80.444, 80.299, 80.151,
          79.999, 79.843, ),
        ( 83.097, 83.169, 83.234, 83.292, 83.343, 83.387, 83.424, 83.454, 83.477, 83.492,
          83.499, 83.499, 83.492, 83.477, 83.454, 83.424, 83.387, 83.343, 83.292, 83.234,
          83.169, 83.097, 83.019, 82.935, 82.845, 82.748, 82.646, 82.539, 82.426, 82.307,
          82.184, 82.056, 81.923, 81.786, 81.644, 81.499, 81.349, 81.195, 81.037, 80.875,
          80.710, 80.541, ),
        ( 84.028, 84.111, 84.187, 84.255, 84.315, 84.367, 84.411, 84.446, 84.472, 84.490,
          84.499, 84.499, 84.490, 84.472, 84.446, 84.411, 84.367, 84.315, 84.255, 84.187,
          84.111, 84.028, 83.937, 83.840, 83.736, 83.626, 83.510, 83.388, 83.260, 83.127,
          82.989, 82.845, 82.698, 82.545, 82.389, 82.228, 82.064, 81.895, 81.723, 81.547,
          81.368, 81.186, ),
        ( 84.932, 85.031, 85.121, 85.203, 85.275, 85.338, 85.391, 85.434, 85.466, 85.488,
          85.499, 85.499, 85.488, 85.466, 85.434, 85.391, 85.338, 85.275, 85.203, 85.121,
          85.031, 84.932, 84.826, 84.712, 84.591, 84.464, 84.330, 84.190, 84.044, 83.894,
          83.738, 83.578, 83.413, 83.244, 83.071, 82.894, 82.714, 82.530, 82.343, 82.153,
          81.959, 81.763, ),
      ), dtype = numpy.float64)
    # longitude centerpoints for the GFDL tripolar grid in the region 20W:20E, 65N:85N
    center_lons = numpy.array( (
        ( -20.000, -19.000, -18.000, -17.000, -16.000, -15.000, -14.000, -13.000, -12.000, -11.000,
          -10.000,  -9.000,  -8.000,  -7.000,  -6.000,  -5.000,  -4.000,  -3.000,  -2.000,  -1.000,
            0.000,   1.000,   2.000,   3.000,   4.000,   5.000,   6.000,   7.000,   8.000,   9.000,
           10.000,  11.000,  12.000,  13.000,  14.000,  15.000,  16.000,  17.000,  18.000,  19.000,
           20.000, ),
        ( -20.009, -19.008, -18.007, -17.006, -16.005, -15.004, -14.004, -13.003, -12.002, -11.001,
          -10.000,  -8.999,  -7.998,  -6.997,  -5.996,  -4.996,  -3.995,  -2.994,  -1.993,  -0.992,
            0.009,   1.010,   2.010,   3.011,   4.012,   5.013,   6.013,   7.014,   8.015,   9.016,
           10.016,  11.017,  12.018,  13.018,  14.019,  15.019,  16.020,  17.021,  18.021,  19.022,
           20.022, ),
        ( -20.036, -19.033, -18.029, -17.026, -16.022, -15.018, -14.015, -13.011, -12.007, -11.004,
          -10.000,  -8.996,  -7.993,  -6.989,  -5.985,  -4.982,  -3.978,  -2.974,  -1.971,  -0.967,
            0.036,   1.040,   2.043,   3.046,   4.050,   5.053,   6.056,   7.059,   8.062,   9.065,
           10.068,  11.071,  12.073,  13.076,  14.078,  15.081,  16.083,  17.085,  18.088,  19.090,
           20.091, ),
        ( -20.085, -19.077, -18.068, -17.060, -16.052, -15.043, -14.035, -13.026, -12.017, -11.009,
          -10.000,  -8.991,  -7.983,  -6.974,  -5.965,  -4.957,  -3.948,  -2.940,  -1.932,  -0.923,
            0.085,   1.093,   2.101,   3.109,   4.116,   5.124,   6.131,   7.139,   8.146,   9.153,
           10.159,  11.166,  12.172,  13.178,  14.184,  15.190,  16.195,  17.200,  18.205,  19.210,
           20.214, ),
        ( -20.158, -19.142, -18.127, -17.111, -16.096, -15.080, -14.064, -13.048, -12.032, -11.016,
          -10.000,  -8.984,  -7.968,  -6.952,  -5.936,  -4.920,  -3.904,  -2.889,  -1.873,  -0.858,
            0.158,   1.173,   2.187,   3.202,   4.216,   5.230,   6.244,   7.257,   8.270,   9.283,
           10.296,  11.308,  12.319,  13.331,  14.342,  15.352,  16.362,  17.372,  18.381,  19.389,
           20.397, ),
        ( -20.258, -19.233, -18.208, -17.182, -16.157, -15.131, -14.105, -13.079, -12.053, -11.026,
          -10.000,  -8.974,  -7.947,  -6.921,  -5.895,  -4.869,  -3.843,  -2.818,  -1.792,  -0.767,
            0.258,   1.282,   2.306,   3.330,   4.354,   5.376,   6.399,   7.421,   8.442,   9.463,
           10.483,  11.503,  12.522,  13.540,  14.558,  15.575,  16.591,  17.607,  18.622,  19.636,
           20.649, ),
        ( -20.390, -19.352, -18.314, -17.276, -16.237, -15.198, -14.159, -13.119, -12.080, -11.040,
          -10.000,  -8.960,  -7.920,  -6.881,  -5.841,  -4.802,  -3.763,  -2.724,  -1.686,  -0.648,
            0.390,   1.427,   2.463,   3.499,   4.534,   5.569,   6.603,   7.636,   8.668,   9.699,
           10.730,  11.759,  12.788,  13.815,  14.842,  15.868,  16.892,  17.915,  18.937,  19.958,
           20.978, ),
        ( -20.558, -19.505, -18.450, -17.395, -16.340, -15.284, -14.227, -13.171, -12.114, -11.057,
          -10.000,  -8.943,  -7.886,  -6.829,  -5.773,  -4.716,  -3.660,  -2.605,  -1.550,  -0.495,
            0.558,   1.611,   2.663,   3.715,   4.765,   5.814,   6.863,   7.910,   8.956,  10.001,
           11.044,  12.086,  13.127,  14.166,  15.204,  16.240,  17.274,  18.307,  19.338,  20.368,
           21.396, ),
        ( -20.770, -19.696, -18.621, -17.545, -16.469, -15.392, -14.314, -13.236, -12.157, -11.079,
          -10.000,  -8.921,  -7.843,  -6.764,  -5.686,  -4.608,  -3.531,  -2.455,  -1.379,  -0.304,
            0.770,   1.843,   2.915,   3.985,   5.054,   6.122,   7.188,   8.253,   9.316,  10.377,
           11.437,  12.494,  13.550,  14.603,  15.655,  16.704,  17.751,  18.796,  19.838,  20.878,
           21.916, ),
        ( -21.032, -19.933, -18.833, -17.731, -16.629, -15.525, -14.421, -13.316, -12.211, -11.106,
          -10.000,  -8.894,  -7.789,  -6.684,  -5.579,  -4.475,  -3.371,  -2.269,  -1.167,  -0.067,
            1.032,   2.130,   3.226,   4.320,   5.412,   6.503,   7.591,   8.677,   9.761,  10.843,
           11.922,  12.998,  14.072,  15.142,  16.210,  17.275,  18.337,  19.396,  20.451,  21.504,
           22.553, ),
        ( -21.355, -20.225, -19.094, -17.961, -16.826, -15.690, -14.553, -13.416, -12.278, -11.139,
          -10.000,  -8.861,  -7.722,  -6.584,  -5.447,  -4.310,  -3.174,  -2.039,  -0.906,   0.225,
            1.355,   2.483,   3.608,   4.732,   5.852,   6.970,   8.086,   9.198,  10.307,  11.413,
           12.515,  13.614,  14.709,  15.801,  16.888,  17.972,  19.051,  20.126,  21.197,  22.264,
           23.327, ),
        ( -21.751, -20.583, -19.414, -18.242, -17.068, -15.893, -14.716, -13.538, -12.359, -11.180,
          -10.000,  -8.820,  -7.641,  -6.462,  -5.284,  -4.107,  -2.932,  -1.758,  -0.586,   0.583,
            1.751,   2.915,   4.077,   5.235,   6.390,   7.542,   8.689,   9.833,  10.972,  12.107,
           13.238,  14.363,  15.484,  16.600,  17.710,  18.815,  19.915,  21.010,  22.098,  23.181,
           24.259, ),
        ( -22.236, -21.023, -19.806, -18.587, -17.365, -16.141, -14.915, -13.688, -12.459, -11.230,
          -10.000,  -8.770,  -7.541,  -6.312,  -5.085,  -3.859,  -2.635,  -1.413,  -0.194,   1.023,
            2.236,   3.445,   4.650,   5.851,   7.048,   8.239,   9.426,  10.607,  11.782,  12.951,
           14.115,  15.272,  16.423,  17.567,  18.704,  19.834,  20.957,  22.073,  23.182,  24.283,
           25.377, ),
        ( -22.831, -21.562, -20.289, -19.012, -17.731, -16.448, -15.161, -13.873, -12.583, -11.292,
          -10.000,  -8.708,  -7.417,  -6.127,  -4.839,  -3.552,  -2.269,  -0.988,   0.289,   1.562,
            2.831,   4.094,   5.353,   6.605,   7.851,   9.091,  10.324,  11.550,  12.768,  13.978,
           15.180,  16.374,  17.559,  18.735,  19.903,  21.062,  22.211,  23.351,  24.481,  25.602,
           26.714, ),
        ( -23.565, -22.228, -20.886, -19.537, -18.184, -16.827, -15.466, -14.102, -12.736, -11.368,
          -10.000,  -8.632,  -7.264,  -5.898,  -4.534,  -3.173,  -1.816,  -0.463,   0.886,   2.228,
            3.565,   4.895,   6.217,   7.532,   8.838,  10.136,  11.424,  12.702,  13.970,  15.228,
           16.475,  17.711,  18.936,  20.149,  21.351,  22.541,  23.719,  24.885,  26.038,  27.180,
           28.310, ),
        ( -24.477, -23.057, -21.629, -20.193, -18.749, -17.300, -15.846, -14.388, -12.927, -11.464,
          -10.000,  -8.536,  -7.073,  -5.612,  -4.154,  -2.700,  -1.251,   0.193,   1.629,   3.057,
            4.477,   5.888,   7.289,   8.678,  10.057,  11.423,  12.777,  14.117,  15.444,  16.757,
           18.056,  19.340,  20.609,  21.864,  23.102,  24.326,  25.534,  26.727,  27.904,  29.066,
           30.212, ),
        ( -25.623, -24.100, -22.565, -21.019, -19.464, -17.899, -16.328, -14.751, -13.170, -11.586,
          -10.000,  -8.414,  -6.830,  -5.249,  -3.672,  -2.100,  -0.536,   1.019,   2.565,   4.100,
            5.623,   7.133,   8.629,  10.110,  11.575,  13.023,  14.454,  15.868,  17.262,  18.638,
           19.995,  21.333,  22.650,  23.948,  25.226,  26.484,  27.723,  28.941,  30.140,  31.319,
           32.479, ),
        ( -27.083, -25.432, -23.764, -22.079, -20.381, -18.670, -16.949, -15.219, -13.483, -11.743,
          -10.000,  -8.257,  -6.517,  -4.781,  -3.051,  -1.330,   0.381,   2.079,   3.764,   5.432,
            7.083,   8.716,  10.328,  11.919,  13.488,  15.033,  16.554,  18.051,  19.523,  20.969,
           22.390,  23.784,  25.152,  26.495,  27.811,  29.102,  30.367,  31.607,  32.822,  34.012,
           35.179, ),
        ( -28.977, -27.166, -25.328, -23.467, -21.584, -19.683, -17.766, -15.836, -13.896, -11.950,
          -10.000,  -8.050,  -6.104,  -4.164,  -2.234,  -0.317,   1.584,   3.467,   5.328,   7.166,
            8.977,  10.762,  12.516,  14.240,  15.932,  17.591,  19.215,  20.806,  22.362,  23.883,
           25.369,  26.820,  28.237,  29.619,  30.968,  32.284,  33.568,  34.819,  36.040,  37.231,
           38.392, ),
        ( -31.494, -29.480, -27.425, -25.334, -23.210, -21.056, -18.876, -16.676, -14.459, -12.232,
          -10.000,  -7.768,  -5.541,  -3.324,  -1.124,   1.056,   3.210,   5.334,   7.425,   9.480,
           11.494,  13.466,  15.394,  17.275,  19.110,  20.897,  22.635,  24.325,  25.966,  27.560,
           29.106,  30.606,  32.060,  33.470,  34.837,  36.162,  37.446,  38.691,  39.898,  41.069,
           42.204, ),
        ( -34.940, -32.671, -30.337, -27.943, -25.493, -22.993, -20.449, -17.869, -15.262, -12.636,
          -10.000,  -7.364,  -4.738,  -2.131,   0.449,   2.993,   5.493,   7.943,  10.337,  12.671,
           14.940,  17.141,  19.274,  21.336,  23.327,  25.247,  27.098,  28.879,  30.594,  32.242,
           33.828,  35.352,  36.817,  38.226,  39.581,  40.884,  42.138,  43.344,  44.506,  45.626,
           46.705, ),
      ), dtype = numpy.float64)
    # latitude centerpoints for the GFDL tripolar grid in the region 20W:20E, 65N:85N
    center_lats = numpy.array( (
        ( 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000,
          65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000,
          65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000,
          65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000, 65.000,
          65.000, ),
        ( 65.985, 65.988, 65.990, 65.993, 65.995, 65.996, 65.998, 65.999, 65.999, 66.000,
          66.000, 66.000, 65.999, 65.999, 65.998, 65.996, 65.995, 65.993, 65.990, 65.988,
          65.985, 65.982, 65.979, 65.975, 65.971, 65.967, 65.962, 65.957, 65.952, 65.946,
          65.941, 65.935, 65.928, 65.922, 65.915, 65.908, 65.900, 65.893, 65.885, 65.877,
          65.868, ),
        ( 66.971, 66.976, 66.981, 66.986, 66.989, 66.993, 66.995, 66.997, 66.999, 67.000,
          67.000, 67.000, 66.999, 66.997, 66.995, 66.993, 66.989, 66.986, 66.981, 66.976,
          66.971, 66.964, 66.958, 66.950, 66.943, 66.934, 66.925, 66.915, 66.905, 66.895,
          66.883, 66.871, 66.859, 66.846, 66.833, 66.818, 66.804, 66.789, 66.773, 66.757,
          66.740, ),
        ( 67.957, 67.965, 67.972, 67.979, 67.984, 67.989, 67.993, 67.996, 67.998, 68.000,
          68.000, 68.000, 67.998, 67.996, 67.993, 67.989, 67.984, 67.979, 67.972, 67.965,
          67.957, 67.948, 67.938, 67.927, 67.915, 67.903, 67.889, 67.875, 67.860, 67.844,
          67.827, 67.810, 67.791, 67.772, 67.752, 67.731, 67.710, 67.687, 67.664, 67.640,
          67.615, ),
        ( 68.943, 68.954, 68.963, 68.972, 68.979, 68.986, 68.991, 68.995, 68.998, 68.999,
          69.000, 68.999, 68.998, 68.995, 68.991, 68.986, 68.979, 68.972, 68.963, 68.954,
          68.943, 68.931, 68.918, 68.904, 68.888, 68.872, 68.854, 68.835, 68.816, 68.795,
          68.773, 68.750, 68.725, 68.700, 68.674, 68.646, 68.618, 68.588, 68.557, 68.526,
          68.493, ),
        ( 69.929, 69.943, 69.955, 69.965, 69.975, 69.982, 69.989, 69.994, 69.997, 69.999,
          70.000, 69.999, 69.997, 69.994, 69.989, 69.982, 69.975, 69.965, 69.955, 69.943,
          69.929, 69.915, 69.898, 69.881, 69.862, 69.841, 69.820, 69.797, 69.772, 69.746,
          69.719, 69.690, 69.660, 69.629, 69.596, 69.562, 69.527, 69.490, 69.452, 69.413,
          69.373, ),
        ( 70.916, 70.932, 70.946, 70.959, 70.970, 70.979, 70.987, 70.992, 70.997, 70.999,
          71.000, 70.999, 70.997, 70.992, 70.987, 70.979, 70.970, 70.959, 70.946, 70.932,
          70.916, 70.898, 70.879, 70.858, 70.836, 70.811, 70.785, 70.758, 70.729, 70.698,
          70.665, 70.631, 70.596, 70.558, 70.520, 70.479, 70.437, 70.393, 70.348, 70.302,
          70.253, ),
        ( 71.902, 71.921, 71.938, 71.952, 71.965, 71.976, 71.984, 71.991, 71.996, 71.999,
          72.000, 71.999, 71.996, 71.991, 71.984, 71.976, 71.965, 71.952, 71.938, 71.921,
          71.902, 71.882, 71.860, 71.835, 71.809, 71.781, 71.751, 71.719, 71.685, 71.650,
          71.612, 71.572, 71.531, 71.488, 71.443, 71.396, 71.347, 71.297, 71.244, 71.190,
          71.134, ),
        ( 72.889, 72.910, 72.929, 72.945, 72.960, 72.972, 72.982, 72.990, 72.996, 72.999,
          73.000, 72.999, 72.996, 72.990, 72.982, 72.972, 72.960, 72.945, 72.929, 72.910,
          72.889, 72.866, 72.840, 72.812, 72.783, 72.750, 72.716, 72.680, 72.641, 72.601,
          72.558, 72.513, 72.466, 72.416, 72.365, 72.312, 72.256, 72.199, 72.139, 72.077,
          72.014, ),
        ( 73.875, 73.899, 73.920, 73.939, 73.955, 73.969, 73.980, 73.989, 73.995, 73.999,
          74.000, 73.999, 73.995, 73.989, 73.980, 73.969, 73.955, 73.939, 73.920, 73.899,
          73.875, 73.849, 73.820, 73.789, 73.755, 73.719, 73.681, 73.640, 73.596, 73.550,
          73.502, 73.452, 73.399, 73.343, 73.286, 73.226, 73.163, 73.099, 73.032, 72.962,
          72.891, ),
        ( 74.860, 74.887, 74.910, 74.931, 74.950, 74.965, 74.978, 74.987, 74.994, 74.999,
          75.000, 74.999, 74.994, 74.987, 74.978, 74.965, 74.950, 74.931, 74.910, 74.887,
          74.860, 74.831, 74.799, 74.764, 74.727, 74.686, 74.643, 74.598, 74.549, 74.498,
          74.445, 74.388, 74.329, 74.268, 74.203, 74.137, 74.067, 73.995, 73.921, 73.844,
          73.764, ),
        ( 75.845, 75.874, 75.900, 75.924, 75.944, 75.961, 75.975, 75.986, 75.994, 75.998,
          76.000, 75.998, 75.994, 75.986, 75.975, 75.961, 75.944, 75.924, 75.900, 75.874,
          75.845, 75.812, 75.777, 75.738, 75.696, 75.652, 75.604, 75.553, 75.500, 75.443,
          75.384, 75.321, 75.256, 75.188, 75.117, 75.043, 74.966, 74.887, 74.805, 74.720,
          74.632, ),
        ( 76.828, 76.860, 76.890, 76.915, 76.938, 76.957, 76.972, 76.984, 76.993, 76.998,
          77.000, 76.998, 76.993, 76.984, 76.972, 76.957, 76.938, 76.915, 76.890, 76.860,
          76.828, 76.792, 76.752, 76.710, 76.664, 76.614, 76.562, 76.506, 76.447, 76.384,
          76.319, 76.250, 76.178, 76.103, 76.025, 75.943, 75.859, 75.772, 75.681, 75.588,
          75.492, ),
        ( 77.809, 77.845, 77.878, 77.906, 77.931, 77.952, 77.969, 77.983, 77.992, 77.998,
          78.000, 77.998, 77.992, 77.983, 77.969, 77.952, 77.931, 77.906, 77.878, 77.845,
          77.809, 77.769, 77.726, 77.679, 77.628, 77.573, 77.515, 77.454, 77.388, 77.320,
          77.247, 77.172, 77.093, 77.010, 76.924, 76.835, 76.743, 76.647, 76.548, 76.446,
          76.341, ),
        ( 78.788, 78.828, 78.864, 78.896, 78.924, 78.947, 78.966, 78.981, 78.991, 78.998,
          79.000, 78.998, 78.991, 78.981, 78.966, 78.947, 78.924, 78.896, 78.864, 78.828,
          78.788, 78.744, 78.696, 78.644, 78.588, 78.528, 78.464, 78.395, 78.324, 78.248,
          78.168, 78.085, 77.998, 77.908, 77.814, 77.716, 77.615, 77.510, 77.402, 77.291,
          77.176, ),
        ( 79.765, 79.809, 79.849, 79.884, 79.915, 79.941, 79.962, 79.979, 79.991, 79.998,
          80.000, 79.998, 79.991, 79.979, 79.962, 79.941, 79.915, 79.884, 79.849, 79.809,
          79.765, 79.716, 79.662, 79.604, 79.542, 79.475, 79.404, 79.329, 79.250, 79.166,
          79.079, 78.987, 78.892, 78.793, 78.690, 78.583, 78.472, 78.358, 78.240, 78.118,
          77.993, ),
        ( 80.736, 80.786, 80.831, 80.870, 80.904, 80.934, 80.957, 80.976, 80.989, 80.997,
          81.000, 80.997, 80.989, 80.976, 80.957, 80.934, 80.904, 80.870, 80.831, 80.786,
          80.736, 80.682, 80.622, 80.558, 80.488, 80.414, 80.335, 80.252, 80.164, 80.072,
          79.976, 79.875, 79.770, 79.661, 79.547, 79.430, 79.309, 79.184, 79.056, 78.923,
          78.788, ),
        ( 81.702, 81.758, 81.808, 81.853, 81.892, 81.925, 81.952, 81.973, 81.988, 81.997,
          82.000, 81.997, 81.988, 81.973, 81.952, 81.925, 81.892, 81.853, 81.808, 81.758,
          81.702, 81.641, 81.574, 81.501, 81.424, 81.341, 81.253, 81.160, 81.063, 80.960,
          80.854, 80.742, 80.626, 80.506, 80.382, 80.253, 80.121, 79.984, 79.844, 79.700,
          79.552, ),
        ( 82.660, 82.723, 82.781, 82.831, 82.876, 82.914, 82.945, 82.969, 82.986, 82.997,
          83.000, 82.997, 82.986, 82.969, 82.945, 82.914, 82.876, 82.831, 82.781, 82.723,
          82.660, 82.590, 82.514, 82.432, 82.344, 82.251, 82.152, 82.049, 81.939, 81.825,
          81.706, 81.583, 81.455, 81.322, 81.185, 81.044, 80.899, 80.750, 80.597, 80.440,
          80.280, ),
        ( 83.604, 83.678, 83.744, 83.803, 83.855, 83.899, 83.935, 83.963, 83.984, 83.996,
          84.000, 83.996, 83.984, 83.963, 83.935, 83.899, 83.855, 83.803, 83.744, 83.678,
          83.604, 83.524, 83.437, 83.343, 83.243, 83.138, 83.026, 82.909, 82.786, 82.658,
          82.525, 82.387, 82.245, 82.098, 81.947, 81.792, 81.633, 81.470, 81.303, 81.133,
          80.959, ),
        ( 84.530, 84.617, 84.695, 84.765, 84.826, 84.879, 84.922, 84.956, 84.980, 84.995,
          85.000, 84.995, 84.980, 84.956, 84.922, 84.879, 84.826, 84.765, 84.695, 84.617,
          84.530, 84.436, 84.335, 84.226, 84.111, 83.989, 83.862, 83.728, 83.589, 83.445,
          83.296, 83.142, 82.984, 82.822, 82.655, 82.485, 82.310, 82.133, 81.951, 81.767,
          81.579, ),
      ), dtype = numpy.float64)
    # model salinity data at the center points of the GFDL tripolar grid in the region 20W:20E, 65N:85N
    # used here only for the land mask (values set to 1.0E20)
    salt_center_data = numpy.array( (
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 34.775, 34.895, 35.043,
          35.134, 35.151, 35.142, 35.128, 35.118, 35.100, 35.085, 35.097, 35.124, 35.151,
          35.173, 35.195, 35.223, 35.254, 35.283, 35.285, 35.258, 35.227, 35.192, 35.157,
          35.125, 35.069, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 34.499, 34.611, 34.769,
          34.864, 34.890, 34.921, 34.959, 34.981, 34.992, 35.018, 35.064, 35.115, 35.150,
          35.170, 35.183, 35.201, 35.228, 35.256, 35.268, 35.261, 35.248, 35.226, 35.185,
          35.129, 35.061, 34.990, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 33.520, 33.618, 33.716, 33.803, 33.887, 33.986, 34.135, 34.307, 34.478, 34.638,
          34.728, 34.782, 34.831, 34.865, 34.880, 34.899, 34.946, 35.023, 35.100, 35.157,
          35.185, 35.196, 35.203, 35.214, 35.230, 35.242, 35.245, 35.242, 35.232, 35.207,
          35.161, 35.099, 35.034, 35.004, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 33.521, 33.613, 33.731, 33.882, 34.050, 34.222, 34.411, 34.558, 34.641, 34.699,
          34.733, 34.755, 34.774, 34.790, 34.814, 34.859, 34.935, 35.035, 35.125, 35.181,
          35.206, 35.213, 35.216, 35.218, 35.223, 35.228, 35.231, 35.232, 35.229, 35.217,
          35.192, 35.153, 35.094, 35.032, 34.987, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 33.439, 33.597, 33.783, 33.992, 34.211, 34.397, 34.538, 34.623, 34.663, 34.681,
          34.690, 34.701, 34.719, 34.752, 34.807, 34.887, 34.982, 35.075, 35.144, 35.185,
          35.204, 35.212, 35.216, 35.218, 35.220, 35.221, 35.221, 35.221, 35.218, 35.209,
          35.189, 35.152, 35.090, 35.021, 34.961, 34.911, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 33.225, 33.418, 33.639, 33.823, 33.985, 34.169, 34.375, 34.522, 34.591, 34.613,
          34.622, 34.639, 34.676, 34.737, 34.815, 34.908, 34.999, 35.071, 35.123, 35.157,
          35.179, 35.192, 35.200, 35.205, 35.206, 35.206, 35.205, 35.203, 35.199, 35.193,
          35.178, 35.145, 35.079, 35.004, 34.950, 34.925, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, ),
        ( 33.024, 33.210, 33.468, 33.712, 33.918, 34.081, 34.237, 34.377, 34.466, 34.512,
          34.545, 34.586, 34.644, 34.719, 34.804, 34.890, 34.962, 35.013, 35.049, 35.078,
          35.104, 35.129, 35.152, 35.170, 35.183, 35.189, 35.189, 35.184, 35.177, 35.168,
          35.152, 35.125, 35.085, 35.029, 34.986, 34.957, 34.919, 34.897, 34.882, 1.0E20,
          1.0E20, ),
        ( 32.896, 33.029, 33.250, 33.533, 33.811, 34.006, 34.117, 34.198, 34.278, 34.362,
          34.451, 34.540, 34.624, 34.699, 34.770, 34.832, 34.879, 34.910, 34.932, 34.957,
          34.989, 35.027, 35.066, 35.102, 35.129, 35.149, 35.160, 35.164, 35.160, 35.149,
          35.135, 35.118, 35.096, 35.068, 35.037, 35.013, 34.988, 34.958, 34.929, 34.906,
          34.892, ),
        ( 32.860, 32.935, 33.105, 33.373, 33.672, 33.922, 34.095, 34.205, 34.284, 34.359,
          34.436, 34.518, 34.603, 34.677, 34.735, 34.777, 34.806, 34.829, 34.851, 34.878,
          34.913, 34.953, 34.994, 35.030, 35.061, 35.089, 35.111, 35.128, 35.136, 35.135,
          35.127, 35.115, 35.101, 35.086, 35.068, 35.047, 35.021, 34.996, 34.972, 34.948,
          34.929, ),
        ( 1.0E20, 32.914, 33.031, 33.245, 33.497, 33.746, 33.972, 34.156, 34.282, 34.368,
          34.433, 34.493, 34.553, 34.618, 34.685, 34.746, 34.791, 34.824, 34.851, 34.876,
          34.902, 34.929, 34.958, 34.986, 35.015, 35.042, 35.066, 35.086, 35.102, 35.110,
          35.111, 35.106, 35.096, 35.083, 35.068, 35.051, 35.034, 35.017, 35.002, 34.988,
          34.974, ),
        ( 1.0E20, 32.894, 32.963, 33.084, 33.233, 33.417, 33.667, 33.911, 34.108, 34.257,
          34.375, 34.473, 34.553, 34.623, 34.694, 34.772, 34.841, 34.882, 34.900, 34.912,
          34.926, 34.943, 34.963, 34.984, 35.004, 35.023, 35.041, 35.058, 35.072, 35.081,
          35.084, 35.082, 35.074, 35.060, 35.040, 35.017, 34.994, 34.975, 34.970, 34.965,
          34.963, ),
        ( 1.0E20, 32.873, 32.904, 32.930, 32.942, 33.084, 33.292, 33.501, 33.682, 33.848,
          34.022, 34.201, 34.352, 34.462, 34.561, 34.678, 34.811, 34.908, 34.943, 34.954,
          34.962, 34.973, 34.985, 34.999, 35.013, 35.027, 35.039, 35.049, 35.056, 35.059,
          35.058, 35.051, 35.038, 35.018, 34.986, 34.938, 34.833, 34.746, 34.756, 34.839,
          34.887, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.745, 32.793, 32.889, 33.012, 33.142, 33.288,
          33.473, 33.691, 33.882, 34.033, 34.174, 34.330, 34.507, 34.703, 34.878, 34.964,
          34.987, 34.997, 35.005, 35.014, 35.021, 35.028, 35.033, 35.036, 35.037, 35.034,
          35.026, 35.012, 34.994, 34.963, 34.882, 34.696, 34.517, 34.458, 34.499, 34.601,
          34.732, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.748, 32.764, 32.805, 32.854, 32.898, 32.955,
          33.041, 33.173, 33.330, 33.495, 33.668, 33.858, 34.067, 34.292, 34.526, 34.764,
          34.942, 34.994, 35.008, 35.014, 35.019, 35.021, 35.022, 35.020, 35.016, 35.010,
          35.003, 34.990, 34.963, 34.883, 34.724, 34.517, 34.403, 34.380, 34.411, 34.477,
          34.587, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.833, 32.839, 32.844, 32.855, 32.861, 32.866,
          32.883, 32.930, 33.015, 33.132, 33.279, 33.458, 33.662, 33.884, 34.113, 34.343,
          34.573, 34.800, 34.959, 34.999, 35.008, 35.012, 35.013, 35.013, 35.012, 1.0E20,
          1.0E20, 1.0E20, 1.0E20, 34.401, 34.380, 34.346, 34.311, 34.298, 34.306, 34.337,
          34.387, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.859, 32.856, 32.839, 32.816, 32.794,
          32.785, 32.801, 32.852, 32.941, 33.068, 33.229, 33.422, 33.635, 33.858, 34.076,
          34.279, 34.469, 34.681, 34.902, 34.984, 35.000, 35.003, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 34.209, 34.218, 34.240, 34.277,
          34.320, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.827, 32.796, 32.730,
          32.686, 32.682, 32.717, 32.794, 32.914, 33.075, 33.272, 33.492, 33.709, 33.916,
          34.107, 34.278, 34.428, 34.585, 34.747, 34.822, 1.0E20, 1.0E20, 1.0E20, 1.0E20,
          1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 34.208, 34.206, 34.209, 34.221, 34.240,
          34.264, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.557,
          32.551, 32.562, 32.605, 32.690, 32.822, 32.999, 33.202, 33.411, 33.610, 33.787,
          33.943, 34.076, 34.186, 34.270, 34.315, 34.291, 34.194, 34.133, 34.099, 34.089,
          34.102, 34.122, 1.0E20, 1.0E20, 1.0E20, 34.229, 34.217, 34.206, 34.201, 34.202,
          34.210, ),
        ( 1.0E20, 1.0E20, 1.0E20, 1.0E20, 1.0E20, 32.417, 32.416, 32.417, 32.419, 32.430,
          32.443, 32.469, 32.520, 32.610, 32.742, 32.912, 33.109, 33.309, 33.493, 33.646,
          33.767, 33.863, 33.938, 33.993, 34.029, 34.039, 34.033, 34.015, 33.998, 33.992,
          34.000, 34.008, 34.009, 34.031, 34.073, 34.127, 34.160, 34.177, 34.186, 34.196,
          34.213, ),
        ( 1.0E20, 1.0E20, 1.0E20, 32.404, 32.397, 32.387, 32.378, 32.371, 32.368, 32.367,
          32.377, 32.404, 32.457, 32.542, 32.660, 32.808, 32.974, 33.145, 33.308, 33.452,
          33.573, 33.672, 33.748, 33.804, 33.844, 33.870, 33.888, 33.902, 33.914, 33.928,
          33.948, 33.973, 34.003, 34.038, 34.076, 34.112, 34.144, 34.172, 34.199, 34.230,
          34.271, ),
        ( 32.486, 32.454, 32.419, 32.385, 32.354, 32.330, 32.312, 32.302, 32.297, 32.300,
          32.311, 32.339, 32.389, 32.462, 32.561, 32.680, 32.812, 32.948, 33.083, 33.208,
          33.322, 33.422, 33.507, 33.577, 33.636, 33.687, 33.733, 33.774, 33.811, 33.846,
          33.881, 33.918, 33.958, 33.999, 34.038, 34.075, 34.113, 34.152, 34.195, 34.243,
          34.300, ),
      ), dtype = numpy.float64)
    # Create the land (True) / ocean (False) centerpoint mask from the salt data 
    over_land = ( salt_center_data >= 256.0 )
    # Synthesize the data values for the curvilinear grid center points
    cos_data = numpy.cos(numpy.deg2rad(center_lons)) * \
               numpy.cos(3.6 * numpy.deg2rad(center_lats - 65.0))
    # Reassign the values that are over land
    cos_data[over_land] = 1.0E20

    # All the data is given as [lat][lon], so return the transpose of the arrays
    return (corner_lons.T, corner_lats.T, center_lons.T, center_lats.T, cos_data.T)


def __createExampleRectData():
    '''
    Creates and returns example longitude, latitudes, and data for a rectilinear 
    grid.  Covers approximately the same region given by __createExampleCurvData.
    Assigns grid center point data[i,j] 
        = cos(lon[i,j]) * cos(3.6 * (lat[i,j] - 65.0)) for areas over ocean, 
        = 1.0E34 for areas over land.

    Arguments:
        None
    Returns: 
        (lon_edges, lat_edges, data) where:
        lon_edges: numpy.float64 1D array of rectilinear edge longitudes
        lat_edges: numpy.float64 1D array of rectilinear edge latitudes
        data:      numpy.float64 2D array of rectilinear center point data values
    '''
    # average annual salinity data at the center points of the rectilinear grid 
    # 19.5W:19.5E:1.0, 65.5N:84.5N:1.0
    # used here only for the land mask (values set to 1.0E34)
    salt_center_data = numpy.array( (
        ( 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 34.502, 34.615, 34.683,
          34.679, 34.714, 34.795, 34.891, 34.908, 34.961, 34.941, 34.976, 35.021, 35.050,
          35.109, 35.159, 35.160, 35.125, 35.112, 34.919, 34.891, 34.981, 34.882, 34.630,
          33.866, 33.155, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 34.018, 1.0E34, 34.321, 1.0E34, 1.0E34, 34.455, 34.534, 34.543, 34.580, 34.650,
          34.716, 34.743, 34.858, 34.939, 34.962, 34.948, 34.987, 34.995, 35.061, 35.073,
          35.108, 35.160, 35.169, 35.138, 35.126, 34.991, 34.986, 34.976, 34.758, 34.708,
          34.511, 33.723, 32.282, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 34.527, 34.459, 34.534, 34.451, 34.449, 34.564, 34.576, 34.618, 34.604, 34.638,
          34.642, 34.699, 34.782, 34.964, 34.977, 34.996, 34.986, 35.012, 35.031, 35.047,
          35.095, 35.123, 35.146, 35.123, 35.122, 35.104, 35.070, 35.092, 34.945, 34.755,
          34.086, 33.745, 33.530, 33.223, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 34.088, 34.272, 34.313, 34.537, 34.617, 34.624, 34.706, 34.673, 34.692, 34.723,
          34.781, 34.867, 34.901, 34.997, 34.999, 35.019, 35.036, 35.051, 35.090, 35.091,
          35.111, 35.116, 35.123, 35.122, 35.121, 35.097, 35.067, 35.022, 35.046, 35.019,
          34.726, 34.435, 34.405, 33.903, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 33.676, 33.810, 34.164, 34.428, 34.597, 34.587, 34.694, 34.722, 34.674, 34.769,
          34.780, 34.780, 34.906, 34.984, 34.912, 35.038, 35.061, 35.073, 35.085, 35.093,
          35.087, 35.122, 35.104, 35.099, 35.116, 35.128, 35.097, 35.084, 35.063, 35.053,
          35.045, 35.027, 34.945, 34.712, 34.448, 34.382, 34.133, 1.0E34, 1.0E34, 1.0E34, ),
        ( 32.305, 32.585, 33.430, 34.153, 34.316, 34.408, 34.473, 34.496, 34.592, 34.787,
          34.694, 34.684, 34.778, 34.670, 34.779, 34.985, 34.933, 35.045, 35.068, 34.976,
          35.076, 35.093, 35.094, 35.101, 35.111, 35.103, 35.107, 35.096, 35.104, 35.095,
          35.093, 35.055, 35.048, 35.004, 35.001, 34.705, 34.402, 34.307, 34.372, 34.294, ),
        ( 33.298, 32.975, 33.267, 33.629, 33.799, 34.054, 33.829, 33.755, 33.696, 34.181,
          34.324, 34.399, 34.318, 34.354, 34.438, 34.553, 34.747, 34.723, 34.806, 34.919,
          34.982, 35.045, 35.055, 35.068, 35.078, 35.096, 35.081, 35.086, 35.075, 35.086,
          35.081, 35.057, 35.044, 35.015, 34.958, 34.824, 34.735, 34.718, 34.728, 34.769, ),
        ( 28.105, 29.990, 31.815, 32.463, 31.622, 33.312, 32.423, 32.791, 32.356, 33.881,
          34.186, 34.055, 34.377, 34.398, 34.367, 34.426, 34.449, 34.416, 34.594, 34.626,
          34.649, 34.733, 34.806, 34.900, 34.951, 35.059, 35.077, 35.033, 35.036, 35.078,
          35.104, 35.068, 35.045, 35.013, 34.973, 34.881, 34.889, 34.967, 34.959, 34.982, ),
        ( 31.406, 32.084, 32.798, 33.643, 32.759, 34.690, 32.999, 31.737, 34.213, 34.307,
          34.486, 34.695, 34.260, 34.275, 33.731, 34.507, 34.299, 34.543, 34.439, 34.526,
          34.578, 34.629, 34.636, 34.700, 34.724, 34.912, 34.976, 34.990, 34.995, 35.086,
          35.085, 35.060, 35.070, 35.051, 35.004, 34.974, 34.948, 34.910, 34.857, 34.917, ),
        ( 1.0E34, 30.750, 27.245, 31.925, 32.227, 34.169, 34.192, 32.716, 34.416, 34.127,
          34.355, 34.446, 34.585, 34.459, 34.368, 34.711, 34.466, 34.565, 34.596, 34.600,
          34.611, 34.630, 34.647, 34.628, 34.709, 34.872, 34.945, 34.983, 35.015, 35.033,
          35.050, 35.048, 35.076, 35.052, 35.058, 35.018, 34.938, 34.635, 34.515, 34.509, ),
        ( 1.0E34, 1.0E34, 1.0E34, 1.0E34, 31.190, 31.372, 32.543, 32.013, 33.165, 33.239,
          33.776, 33.138, 33.716, 33.752, 33.990, 34.530, 34.435, 34.529, 34.473, 34.644,
          34.588, 34.683, 34.666, 34.722, 34.650, 34.775, 34.690, 34.951, 34.748, 34.986,
          34.926, 34.908, 34.950, 34.993, 34.709, 34.704, 34.556, 34.493, 34.461, 34.363, ),
        ( 1.0E34, 1.0E34, 30.850, 29.813, 30.600, 30.757, 29.950, 31.813, 33.114, 29.808,
          31.363, 32.004, 33.087, 33.194, 33.541, 33.219, 33.639, 34.460, 33.944, 34.465,
          34.410, 34.328, 34.559, 34.619, 34.736, 34.820, 34.931, 34.976, 34.959, 34.978,
          34.939, 34.995, 34.793, 34.584, 34.382, 33.950, 1.0E34, 33.794, 34.030, 34.131, ),
        ( 1.0E34, 1.0E34, 30.732, 29.499, 29.585, 29.906, 30.385, 29.942, 30.701, 31.643,
          30.812, 32.183, 31.762, 31.644, 31.312, 32.599, 33.452, 33.868, 34.386, 34.501,
          34.668, 34.623, 34.619, 34.811, 34.744, 34.906, 34.890, 34.939, 34.919, 34.773,
          34.619, 34.328, 33.889, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 33.359, ),
        ( 1.0E34, 1.0E34, 30.836, 31.386, 30.957, 30.987, 30.169, 29.891, 30.260, 30.652,
          31.087, 30.988, 30.675, 30.949, 31.426, 31.795, 32.825, 33.460, 33.803, 34.377,
          34.052, 34.130, 34.269, 34.091, 34.316, 34.466, 34.559, 34.429, 34.310, 34.326,
          33.749, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 1.0E34, 1.0E34, 1.0E34, 31.548, 31.176, 30.850, 30.800, 30.382, 30.196, 30.663,
          30.157, 30.553, 30.538, 31.745, 31.467, 34.325, 32.348, 32.389, 32.391, 32.426,
          33.053, 33.440, 33.754, 34.092, 34.098, 34.181, 34.494, 34.042, 34.519, 34.437,
          33.853, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, ),
        ( 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 30.153, 30.359, 30.328, 30.670, 30.451,
          31.039, 32.220, 32.273, 31.958, 32.034, 32.082, 32.200, 32.108, 32.116, 32.294,
          32.758, 33.232, 33.337, 33.485, 33.391, 33.403, 33.847, 33.087, 33.505, 33.622,
          32.403, 34.123, 33.898, 34.422, 34.132, 33.988, 33.674, 33.688, 1.0E34, 1.0E34, ),
        ( 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 30.939, 31.403,
          30.826, 30.750, 31.006, 30.940, 31.011, 31.304, 31.941, 31.769, 29.121, 23.200,
          32.445, 33.454, 33.141, 33.831, 33.980, 33.775, 33.204, 33.365, 33.386, 33.333,
          32.736, 32.677, 33.089, 34.106, 34.156, 33.509, 33.732, 33.290, 33.623, 32.771, ),
        ( 1.0E34, 1.0E34, 1.0E34, 30.818, 1.0E34, 31.268, 31.090, 30.944, 31.070, 31.003,
          31.950, 31.340, 29.934, 32.188, 32.185, 1.0E34, 1.0E34, 32.298, 1.0E34, 32.601,
          33.448, 33.656, 1.0E34, 1.0E34, 1.0E34, 33.991, 33.329, 34.127, 33.703, 32.428,
          33.421, 33.633, 33.228, 33.841, 33.923, 1.0E34, 1.0E34, 32.853, 1.0E34, 1.0E34, ),
        ( 1.0E34, 1.0E34, 1.0E34, 32.490, 1.0E34, 31.849, 31.168, 32.160, 30.490, 1.0E34,
          31.953, 32.030, 32.474, 32.373, 1.0E34, 32.130, 1.0E34, 1.0E34, 32.440, 32.559,
          1.0E34, 1.0E34, 1.0E34, 31.751, 1.0E34, 32.795, 32.864, 32.936, 32.800, 33.676,
          33.670, 1.0E34, 33.023, 33.761, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 33.290, 33.543, ),
        ( 32.120, 32.370, 1.0E34, 31.970, 1.0E34, 31.880, 31.790, 32.100, 31.580, 31.684,
          31.727, 31.768, 32.365, 32.332, 32.380, 1.0E34, 1.0E34, 32.598, 1.0E34, 1.0E34,
          1.0E34, 31.811, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 1.0E34,
          1.0E34, 1.0E34, 33.465, 1.0E34, 1.0E34, 1.0E34, 1.0E34, 31.944, 1.0E34, 1.0E34, ),
    ), dtype = numpy.float64)
    # Rectilinear grid longitude edges covering center points 19.5W:19.5E:1.0
    lon_edges = numpy.linspace(-20.0, 20.0, 41)
    # Rectilinear grid latitude edges covering center points 65.5N:84.5N:1.0
    lat_edges = numpy.linspace(65.0, 85.0, 21)
    # Compute the center point longitudes and latitudes from the edges
    mid_lons = 0.5 * (lon_edges[:-1] + lon_edges[1:])
    mid_lats = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    # Synthesize the data values for the rectilinear grid center points
    center_lons, center_lats = numpy.meshgrid(mid_lons, mid_lats)
    sin_cos_data = numpy.cos(numpy.deg2rad(center_lons)) * \
                   numpy.cos(3.6 * numpy.deg2rad(center_lats - 65.0))
    # Reassign the values that are over land
    over_land = ( salt_center_data >= 256.0 )
    sin_cos_data[over_land] = 1.0E34

    # The 2D arrays were generated as [lat][lon], so return the transpose
    return (lon_edges, lat_edges, sin_cos_data.T)


def __printDiffs(grid_lons, grid_lats, undef_val, expect_data, found_data):
    '''
    Prints significant differences between expect_data and found_data
    along with the location of these differences
    
    Arguments:
        grid_lons:   numpy 2D array of grid longitudes
        grid_lats:   numpy 2D array of grid latitudes
        undef_val:   numpy array of one value; the undefined data value
        expect_data: numpy 2D array of expected data values
        found_data:  numpy 2d array of data values to check
    Returns: 
        None
    Raises:
        ValueError:  if the array shapes do not match
    '''
    if ( len(grid_lons.shape) != 2 ):
        raise ValueError("grid_lons is not 2D")
    if ( grid_lats.shape != grid_lons.shape ):
        raise ValueError("grid_lats.shape != grid_lons.shape")
    if ( expect_data.shape != grid_lons.shape ):
        raise ValueError("expect_data.shape != grid_lons.shape")
    if ( found_data.shape != grid_lons.shape ):
        raise ValueError("found_data.shape != grid_lons.shape")
    different = ( numpy.abs(expect_data - found_data) > 0.05 )
    diff_lons = grid_lons[different]
    diff_lats = grid_lats[different]
    diff_expect = expect_data[different]
    diff_found = found_data[different]
    diff_list = [ ]
    for (lon, lat, expect, found) in zip(diff_lons, diff_lats, diff_expect, diff_found):
        if expect == undef_val:
            # most serious - should have been masked out
            diff_list.append([2, lon, lat, expect, found])
        elif found == undef_val:
            # least serious - destination not covered by source
            diff_list.append([0, lon, lat, expect, found])
        else:
            # might be of concern
            diff_list.append([1, lon, lat, expect, found])
    # order primarily from least to most serious, 
    # secondarily smallest to largest longitude,
    # tertiarily smallest to largest latitude
    diff_list.sort()
    num_not_undef = 0
    num_undef = 0
    num_diff = 0
    for (_, lon, lat, expect, found) in diff_list:
        if expect == undef_val:
            num_not_undef += 1
            print "lon = %#7.3f, lat = %7.3f, expect =  undef, found = %#6.3f" \
                  % (lon, lat, found)
        elif found == undef_val:
            num_undef += 1
            print "lon = %#7.3f, lat = %7.3f, expect = %#6.3f, found =  undef" \
                  % (lon, lat, expect)
        else:
            num_diff += 1
            print "lon = %#7.3f, lat = %7.3f, expect = %#6.3f, found = %#6.3f, " \
                  "diff = %#6.3f" % (lon, lat, expect, found, found - expect)
    print "%3d undefined when defined expected" % num_undef
    print "%3d with absolute difference > 0.05" % num_diff
    print "%3d defined when undefined expected" % num_not_undef
    print "%3d values in the grid" % (expect_data.shape[0] * expect_data.shape[1])


# main routine - for testing "by hand"
if __name__ == '__main__':
    try:
        while True:
            print 'cw2r: curvilinear with corners to rectilinear'
            print 'co2r: curvilinear without corners to rectilinear'
            print 'r2cw: rectilinear to curvilinear with corners'
            print 'r2co: rectilinear to curvilinear without corners'
            print 'Ctrl-D to quit'
            direction = raw_input('Regrid test to run? ')
            direction = direction.strip().lower()
            if direction in ('cw2r', 'co2r', 'r2cw', 'r2co'):
                break
    except EOFError:
        raise SystemExit(0)
 
    # Synthesize test data
    (curv_corner_lons, curv_corner_lats, 
     curv_center_lons, curv_center_lats, curv_data) = __createExampleCurvData()
    curv_center_ignore = ( curv_data >= 256.0 ) 
    (rect_lon_edges, rect_lat_edges, rect_data) = __createExampleRectData()
    rect_center_ignore = ( rect_data >= 256.0 )
    undef_val = numpy.array([-1.0E10], dtype=numpy.float64)

    # Create the expected results on the curvilinear grid
    curv_expect_data = curv_data.copy()
    curv_expect_data[curv_center_ignore] = undef_val

    # Create the expected results on the rectilinear grid
    rect_expect_data = rect_data.copy()
    rect_expect_data[rect_center_ignore] = undef_val

    # Generate the 2D rectilinear longitudes and latitudes arrays only to 
    # simplify printing differences; not used for generating rectilinear grids
    rect_mid_lons = 0.5 * (rect_lon_edges[:-1] + rect_lon_edges[1:])
    rect_mid_lats = 0.5 * (rect_lat_edges[:-1] + rect_lat_edges[1:])
    rect_center_lats, rect_center_lons = numpy.meshgrid(rect_mid_lats, rect_mid_lons)

    # Initialize ESMP
    ESMP.ESMP_Initialize()

    # Create the regridder
    regridder = Ferret2DRegridder()

    if direction in ('cw2r', 'r2cw'):
        # Create the curvilinear grid with corner and center points
        regridder.createCurvGrid(curv_center_lons, curv_center_lats, curv_center_ignore, 
                                 curv_corner_lons, curv_corner_lats)
    elif direction in ('co2r', 'r2co'):
        # Create the curvilinear grid with only center points
        regridder.createCurvGrid(curv_center_lons, curv_center_lats, curv_center_ignore)
    else:
        raise ValueError("unexpected direction of %s" % direction)

    # Create the rectilinear grid with corner and center points
    regridder.createRectGrid(rect_lon_edges, rect_lat_edges, rect_center_ignore)

    if direction in ('cw2r', 'co2r'):
        print ""
        if direction == 'cw2r':
            print "Examining rectilinear results from curvilinear with corners"
        else:
            print "Examining rectilinear results from curvilinear without corners"

        # Create the curvilinear source field
        regridder.assignCurvField(curv_data)

        # Create the rectilinear destination field
        regridder.assignRectField()

        # Regrid from curvilinear to rectilinear using the bilinear method
        rect_regrid_data = regridder.regridCurvToRect(undef_val, ESMP.ESMP_REGRIDMETHOD_BILINEAR)

        # Print the differences between the expected and regrid data
        print ""
        print "analytic (expect) versus bilinear regridded (found) differences"
        __printDiffs(rect_center_lons, rect_center_lats, undef_val,
                     rect_expect_data, rect_regrid_data)

        # Regrid from curvilinear to rectilinear using the patch method
        rect_regrid_data = regridder.regridCurvToRect(undef_val, ESMP.ESMP_REGRIDMETHOD_PATCH)

        # Print the differences between the expected and regrid data
        print ""
        print "analytic (expect) versus patch regridded (found) differences"
        __printDiffs(rect_center_lons, rect_center_lats, undef_val,
                     rect_expect_data, rect_regrid_data)

        if direction == 'cw2r':
            # Regrid from curvilinear to rectilinear using the conserve method
            # Corners required for this method
            rect_regrid_data = regridder.regridCurvToRect(undef_val, ESMP.ESMP_REGRIDMETHOD_CONSERVE)

            # Print the differences between the expected and regrid data
            print ""
            print "analytic (expect) versus conserve regridded (found) differences"
            __printDiffs(rect_center_lons, rect_center_lats, undef_val,
                         rect_expect_data, rect_regrid_data)

    elif direction in ('r2cw', 'r2co'):
        print ""
        if direction == 'r2cw':
            print "Examining curvilinear with corners results from rectilinear"
        else:
            print "Examining curvilinear without corners results from rectilinear"

        # Create the rectilinear source field
        regridder.assignRectField(rect_data)

        # Create the curvilinear destination field
        regridder.assignCurvField(None)

        # Regrid from rectilinear to curvilinear using the bilinear method
        curv_regrid_data = regridder.regridRectToCurv(undef_val, ESMP.ESMP_REGRIDMETHOD_BILINEAR)

        # Print the differences between the expected and regrid data
        print ""
        print "analytic (expect) versus bilinear regridded (found) differences"
        __printDiffs(curv_center_lons, curv_center_lats, undef_val,
                     curv_expect_data, curv_regrid_data)

        # Regrid from rectilinear to curvilinear using the patch method
        curv_regrid_data = regridder.regridRectToCurv(undef_val, ESMP.ESMP_REGRIDMETHOD_PATCH)

        # Print the differences between the expected and regrid data
        print ""
        print "analytic (expect) versus patch regridded (found) differences"
        __printDiffs(curv_center_lons, curv_center_lats, undef_val,
                     curv_expect_data, curv_regrid_data)

        if direction == 'r2cw':
            # Regrid from rectilinear to curvilinear using the conserve method
            # Corners required for this method
            curv_regrid_data = regridder.regridRectToCurv(undef_val, ESMP.ESMP_REGRIDMETHOD_CONSERVE)

            # Print the differences between the expected and regrid data
            print ""
            print "analytic (expect) versus conserve regridded (found) differences"
            __printDiffs(curv_center_lons, curv_center_lats, undef_val,
                         curv_expect_data, curv_regrid_data)

    else:
        raise ValueError("unexpected direction of %s" % direction)

    # Done with this regridder
    regridder.finalize()

    # Done with ESMP    
    ESMP.ESMP_Finalize()


