"""
Returns histogram bin counts for a given array of values.
"""
import numpy
import pyferret

# The following is just to circumvent to call to pyferret.get_axis_info for testing
DOING_UNIT_TEST = False

def ferret_init(id):
    """
    Initialization for the stats_fit python-backed ferret external function
    """
    retdict = { "numargs": 2,
                "descript": "Returns unweighted histogram bin counts for all defined data values",
                "axes": ( pyferret.AXIS_IMPLIED_BY_ARGS,
                          pyferret.AXIS_IMPLIED_BY_ARGS,
                          pyferret.AXIS_IMPLIED_BY_ARGS,
                          pyferret.AXIS_IMPLIED_BY_ARGS, ),
                "argnames": ( "VALS", "BINS_TEMPLATE", ),
                "argdescripts": ( "Values to put into bins and then count",
                                  "Template argument whose one defined axis gives midpoints of bins", ),
                "argtypes": ( pyferret.FLOAT_ARG, pyferret.FLOAT_ARG, ),
                "influences": ( ( False, False, False, False, ),
                                ( True,  True,  True,  True, ), ),
              }
    return retdict


def ferret_compute(id, result, resbdf, inputs, inpbdfs):
    """
    Assigns result with histogram bin counts of data in inputs[0].  Bin
    limits are defined using the values of the one defined non-singular
    axis associated with inputs[1].  The argument inputs[1] is otherwise
    unused.  Undefined values in inputs[0] are eliminated before binning.
    """
    # get the box limits of the one defined non-singular axis of the second argument
    if DOING_UNIT_TEST:
        limits_func = my_get_box_limits
    else:
        limits_func = pyferret.get_axis_box_limits
    limits_tuple = None
    axis_used = None
    for axis_num in ( pyferret.X_AXIS, pyferret.Y_AXIS, pyferret.Z_AXIS, pyferret.T_AXIS):
        this_tuple = limits_func(id, pyferret.ARG2, axis_num)
        if (this_tuple != None) and (len(this_tuple[0]) > 1):
            if limits_tuple != None:
               raise ValueError("BINS_TEMPLATE has more than one defined non-singular axis")
            limits_tuple = this_tuple
            axis_used = axis_num
    if limits_tuple == None:
        raise ValueError("BINS_TEMPLATE does not have a defined non-singular axis")
    # get the histogram bin limits from the axis box limits
    if not numpy.allclose(limits_tuple[0][1:], limits_tuple[1][:-1]):
        raise ValueError("Unexpected error: gaps exist between axis box limits")
    bin_limits = numpy.empty( ( len(limits_tuple[1]) + 1, ), dtype=numpy.float64)
    bin_limits[0] = limits_tuple[0][0]
    bin_limits[1:] = limits_tuple[1]
    # get the clean data as a flattened array
    badmask = ( numpy.fabs(inputs[0] - inpbdfs[0]) < 1.0E-5 )
    badmask = numpy.logical_or(badmask, numpy.isnan(inputs[0]))
    goodmask = numpy.logical_not(badmask)
    values = inputs[0][goodmask]
    # compute the histogram and assign the counts to result
    (hist, edges) = numpy.histogram(values, bins=bin_limits)
    if axis_used == pyferret.X_AXIS:
        result[:,0,0,0] = hist
    elif axis_used == pyferret.Y_AXIS:
        result[0,:,0,0] = hist
    elif axis_used == pyferret.Z_AXIS:
        result[0,0,:,0] = hist
    elif axis_used == pyferret.T_AXIS:
        result[0,0,0,:] = hist
    else:
        raise ValueError("Unexpected axis_used value: %d" % axis_used)


#
# The rest of this is just for testing this module at the command line
#
if __name__ == "__main__":
    DOING_UNIT_TEST = True
    # create the my_get_box_limits function for testing
    def my_get_box_limits(id, argnum, axisnum):
        if id != 0:
            raise ValueError("Unexpected my_get_box_limits argnum; expected: 0, found: %d" % \
                              argnum)
        if argnum != pyferret.ARG2:
            raise ValueError("Unexpected my_get_box_limits argnum; expected: %d, found: %d" % \
                              (pyferret.ARG2, argnum))
        if axisnum != pyferret.Z_AXIS:
            return None
        limits = numpy.array([1.0, 2.0, 3.0, 4.0, 6.0, 9.0], dtype=numpy.float64)
        return (limits[:-1], limits[1:])
    # create the input values array
    values = numpy.arange(0.0, 10.11, 0.1, dtype=numpy.float32).reshape((1,6,1,17), order='F')
    # create the expected results array
    expected = -1.0 * numpy.ones((1,1,5,1), dtype=numpy.float32, order='F')
    expected[0,0,:,0] = (10.0, 10.0, 10.0, 20.0, 31.0)
    # make sure no errors when ferret_init called
    info = ferret_init(0)
    # make the call to ferret_compute
    result = 999.0 * expected
    resbdf = numpy.array([-1.0], dtype=numpy.float32)
    inpbdfs = numpy.array([-1.0, -1.0], dtype=numpy.float32)
    inputs = ( values, None, )
    ferret_compute(0, result, resbdf, inputs, inpbdfs)
    # verify the results
    if not numpy.allclose(result, expected):
        raise ValueError("Unexpected results; expected:\n%s\nfound:\n%s" % (str(expected), str(result)))
    print "Success"

