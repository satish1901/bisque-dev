###############################################################################
##  BisQue                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2015 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################

"""
Table base for importerters

"""

__author__    = "Dmitry Fedorov <dima@dimin.net>"
__version__   = "1.0"
__copyright__ = "Center for Bio-Image Informatics, University of California at Santa Barbara"

# default imports
import os
import logging
import pkg_resources
import itertools
from pylons.controllers.util import abort
from collections import namedtuple, OrderedDict
import re
import types
import copy

try:
    import ply.yacc as yacc
    import ply.lex as lex
    from ply.lex import TOKEN
except:
    import yacc as yacc
    import lex as lex
    from lex import TOKEN
    
log = logging.getLogger("bq.table.base")

try:
    import numpy as np
except ImportError:
    log.info('Numpy was not found but required for table service!')

try:
    import tables
except ImportError:
    log.info('Tables was not found but required for table service!')

try:
    import pandas as pd
except ImportError:
    log.info('Pandas was not found but required for table service!')


__all__ = [ 'TableBase' ]



#---------------------------------------------------------------------------------------
# Abstract table query language
#---------------------------------------------------------------------------------------

OrConditionTuple = namedtuple('OrConditionTuple', ['left', 'right'])
AndConditionTuple = namedtuple('AndConditionTuple', ['left', 'right'])
ConditionTuple = namedtuple('ConditionTuple', ['left', 'comp', 'right'])
CellSelectionTuple = namedtuple('CellSelectionTuple', ['selectors', 'agg', 'alias'])
SelectorTuple = namedtuple('SelectorTuple', ['dimname', 'dimvalues'])


#---------------------------------------------------------------------------------------
# Supported aggregation functions
#---------------------------------------------------------------------------------------

def _get_agg_fct(agg):
    return {
            'mean': np.mean,
            'avg': np.average,
            'min': np.min,
            'max': np.max,
            'median': np.median,
            'std': np.std
           }.get(agg)

def _check_aggfct(agg):
    if _get_agg_fct(agg) is not None:
        return agg
    else:
        raise ParseError("Unknown aggregation function: '%s'" % agg)

#---------------------------------------------------------------------------------------
# Array/Table wrapper
#---------------------------------------------------------------------------------------

class ArrayOrTable(object):
    def __init__(self, arr, arr_type=None, shape=None, columns=None, cb=None):
        # arr can be DataFrame, pytables array, or pytables table
        # OR provide callback fct to obtain one of those types based on slices provided
        assert arr is None or isinstance(arr, pd.core.frame.DataFrame) or isinstance(arr, tables.table.Table) or isinstance(arr, tables.array.Array)
        if arr is not None:
            self.arr = arr
            self.arr_type = type(arr)
            self.shape = arr.shape
            self.columns = arr.columns.tolist() if isinstance(arr, pd.core.frame.DataFrame) else (arr.colnames if isinstance(arr, tables.table.Table) else None)
            self.cb = None
        else:
            self.arr = None
            self.arr_type = arr_type
            self.shape = shape
            self.columns = columns
            self.cb = cb
        if self.arr_type == tables.array.ImageArray:
            # treat image array like a regular array (for purposes of queries)
            self.arr_type = tables.array.Array
        assert self.arr_type in [pd.core.frame.DataFrame, tables.table.Table, tables.array.Array]
        
    def is_dataframe(self):
        return self.arr_type == pd.core.frame.DataFrame
    
    def is_table(self):
        return self.arr_type == tables.table.Table
    
    def is_array(self):
        return self.arr_type == tables.array.Array
    
    def get_arr(self):
        return self.arr
    
    def get_shape(self):
        return self.shape
    
    def get_slices(self, sels, cond):
        slices = None
        if sels is not None:
            for sel in sels:
                add_slices = self._selectors_to_slices(sel.selectors)
                slices = add_slices if slices is None else self._or_slices(slices, add_slices)
        add_slices = self._cond_to_slices(cond)
        slices = add_slices if slices is None else self._and_slices(slices, add_slices)
        return slices
    
    def get_slice_iter(self, slices, cond, want_cell_coord=False):
        offsets = [0]*len(slices)
        
        if self.arr is None:
            # need to bring in data first
            self.arr = self.cb(slices)
            self.arr_type = type(self.arr)
            assert self.arr_type in [pd.core.frame.DataFrame, tables.table.Table, tables.array.Array]
            # adjust slices to start from 0 since it is already sliced and remember offsets
            for d in xrange(len(slices)):
                offsets[d] = slices[d].start
            slices = tuple([slice(0, slices[d].stop-slices[d].start) for d in xrange(len(slices))])    
        
        ###### translator for And/Or/Condition:
        #    => ( (tuple(coord), node[tuple(coord)]) for coord in np.argwhere((node[Ellipsis] > 0.0) & mask_of_subset & (node[Ellipsis] > 0.0) & mask2_of_subset) )  FOR ARRAY                   OR
        #    => ( ((coord[0],), node.iloc[coord[0]]) for coord in np.argwhere((node[:]['H'] > 0) & (node[:]['L'] > 0)) )                                             FOR TABLE (IF DataFrame)    OR
        #    => ( ((row.nrow,), row) for row in node.where('(H > 0) & (L > 0)') )                                                                                    FOR TABLE (IF pytables)
        filter_exp = None
        if cond is not None:
            if self.is_dataframe():
                filter_exp = self._gen_dataframe_filter(self.arr.iloc[slices[0]], cond)
            elif self.is_table():
                filter_exp = self._gen_table_filter(self.arr, cond)
            elif self.is_array():
                filter_exp = self._gen_array_filter(self.arr[slices], slices, cond)
        
        if filter_exp is None:
            if self.is_dataframe():
                if want_cell_coord:
                    row_iter = ( ((row[0]+offsets[0],), row[1]) for row in self.arr.iloc[slices].iterrows() )
                else:
                    row_iter = ( row[1] for row in self.arr.iloc[slices].iterrows() )
            elif self.is_table():
                if want_cell_coord:
                    row_iter = ( ((row.nrow+offsets[0],), row) for row in self.arr.iterrows(slices[0].start, slices[0].stop) )
                else:
                    row_iter = self.arr.iterrows(slices[0].start, slices[0].stop)
            elif self.is_array():
                if want_cell_coord:
                    # this is very slow for large arrays; avoid!
                    ranges = (xrange(slices[d].start, slices[d].stop) for d in xrange(len(self.arr.shape)))
                    row_iter = ( (tuple([coord[d]+offsets[d] for d in xrange(len(coord))]), self.arr[coord]) for coord in itertools.product(*ranges) )
                else:
                    row_iter = ( self.arr[slices] for x in [1] )
        else:
            # have condition
            if self.is_dataframe():
                if want_cell_coord:
                    row_iter = ( ((coord[0]+slices[0].start+offsets[0],), self.arr.iloc[(coord[0]+slices[0].start, slices[1])]) for coord in np.argwhere(filter_exp) )
                else:
                    row_iter = ( self.arr.iloc[coord[0]+slices[0].start] for coord in np.argwhere(filter_exp) )
            elif self.is_table():
                if want_cell_coord:
                    row_iter = ( ((row.nrow+offsets[0],), row) for row in self.arr.where(filter_exp) if row.nrow >= slices[0].start and row.nrow < slices[0].stop )
                else:
                    row_iter = ( row for row in self.arr.where(filter_exp) if row.nrow >= slices[0].start and row.nrow < slices[0].stop )
            elif self.is_array():
                if want_cell_coord:
                    # this is very slow for large arrays; avoid!
                    row_iter = ( (tuple([coord[d]+slices[d].start+offsets[d] for d in xrange(len(slices))]), self.arr[slices][tuple(coord)]) for coord in np.argwhere(filter_exp) )
                else:
                    row_iter = ( self.arr[slices][filter_exp] for x in [1] )
                    
        return row_iter
    
    def get_sels_iter(self, row_iter, sels, want_cell_coord=False):
        ###### translator for CellSelection:
        #    => np.mean(r[slices])   where r from FILTER                        IF pytables array OR
        #    => np.mean([r['K'] for r in <rowlist from FILTER or ALL>])         IF pytables table OR
        #    => np.mean([r.loc['K'] for r in <rowlist from FILTER or ALL>])     IF pandas Series
        if sels is None:
            # no selection, include all columns
            if self.is_dataframe():
                sel_fct = lambda row: OrderedDict( (colname,row[colname]) for colname in row.keys() )
            elif self.is_table():
                sel_fct = lambda row: OrderedDict( (colname,row[colname]) for colname in self.arr.colnames )
            elif self.is_array():
                sel_fct = lambda row: row
            if want_cell_coord:
                row_iter = ( OrderedDict(sel_fct(row), index=coord) for (coord, row) in row_iter )
            else:
                row_iter = ( sel_fct(row) for row in row_iter )
                
        elif sels[0].agg is None:
            # no aggregation, just return slices
            def sel_fct_df(row):
                res = OrderedDict()
                selix = 0
                for sel in sels:
                    cols = self._selectors_to_columns(sel.selectors)
                    for col_ix in xrange(len(cols)):
                        alias = sel.alias or cols[col_ix]
                        if alias in res:
                            alias = "%s_%s" % (alias, selix)
                        res[alias] = row.loc[cols[col_ix]]
                    selix += 1
                return res
                
            def sel_fct_tb(row):
                res = OrderedDict()
                selix = 0
                for sel in sels:
                    cols = self._selectors_to_columns(sel.selectors)
                    for col_ix in xrange(len(cols)):
                        alias = sel.alias or cols[col_ix]
                        if alias in res:
                            alias = "%s_%s" % (alias, selix)
                        res[alias] = row[cols[col_ix]]
                    selix += 1
                return res
                
            if self.is_dataframe():
                sel_fct = sel_fct_df
            elif self.is_table():
                sel_fct = sel_fct_tb
            elif self.is_array():
                # TODO: how about ALIAS??
                sel_fct = lambda row: row
            if want_cell_coord:
                row_iter = ( OrderedDict(sel_fct(row), index=coord) for (coord, row) in row_iter )
            else:
                row_iter = ( sel_fct(row) for row in row_iter )
                
        else:
            # with aggregation => apply agg fct
            # TODO: find a way to not keep all in memory (push down agg into kernel)
            row_iters_vals_map = OrderedDict()
            row_iters_agg_map = OrderedDict()
            for row in row_iter:
                res = OrderedDict()
                res_agg = OrderedDict()
                selix = 0
                for sel in sels:
                    if self.is_dataframe():
                        cols = self._selectors_to_columns(sel.selectors)
                        for col_ix in xrange(len(cols)):
                            alias = sel.alias or cols[col_ix]
                            if alias in res:
                                alias = "%s_%s" % (alias, selix)
                            res[alias] = row.loc[cols[col_ix]]
                            res_agg[alias] = sel.agg
                    elif self.is_table():
                        cols = self._selectors_to_columns(sel.selectors)
                        for col_ix in xrange(len(cols)):
                            alias = sel.alias or cols[col_ix]
                            if alias in res:
                                alias = "%s_%s" % (alias, selix)
                            res[alias] = row[cols[col_ix]]
                            res_agg[alias] = sel.agg
                    elif self.is_array():
                        alias = sel.alias or "agg%s"%selix
                        res[alias] = row
                        res_agg[alias] = sel.agg
                    selix += 1
                for alias in res:
                    row_iters_vals_map.setdefault(alias, []).append(res[alias])
                    row_iters_agg_map[alias] = res_agg[alias]
                        
            res = OrderedDict( (alias,_get_agg_fct(row_iters_agg_map[alias])(row_iters_vals_map[alias])) for alias in row_iters_vals_map.keys() )
            row_iter = ( res for x in [1] )  # wrap in generator
            
        return row_iter

    def _cond_to_slices(self, cond):
        if isinstance(cond, OrConditionTuple) or isinstance(cond, AndConditionTuple):
            # OR to keep all referenced cells
            return self._or_slices(self._cond_to_slices(cond.left), self._cond_to_slices(cond.right))
        elif isinstance(cond, ConditionTuple):
            return self._cond_to_slices(cond.left)
        elif isinstance(cond, CellSelectionTuple):
            return self._selectors_to_slices(cond.selectors)
        return tuple([ slice(0,self.shape[dim]) for dim in range(len(self.shape)) ])

    def _or_slices(self, slices1, slices2):
        # essentially compute "bounding" slice around slices
        res = [None] * len(slices1)
        for dim in range(len(slices1)):
            res[dim] = slice(min(slices1[dim].start, slices2[dim].start), max(slices1[dim].stop, slices2[dim].stop))
        return tuple(res)
        
    def _and_slices(self, slices1, slices2):
        # compute intersection of slices BUT keep all 'column'/'fields' if Dataframe
        # (this is an artifact of treating fields like dimensions, which they really aren't) 
        res = [None] * len(slices1)
        for dim in range(len(slices1)):
            if self.is_dataframe() and dim == 1:
                res[dim] = slice(min(slices1[dim].start, slices2[dim].start), max(slices1[dim].stop, slices2[dim].stop))
            else:
                res[dim] = slice(max(slices1[dim].start, slices2[dim].start), min(slices1[dim].stop, slices2[dim].stop))
        return tuple(res)

    def _selectors_to_columns(self, sels):
        res = []
        if sels is not None:
            for sel in sels:
                dim = self._get_dim(sel.dimname)
                if dim == 1:
                    if len(sel.dimvalues) == 0 or all([colname is None for colname in sel.dimvalues]):
                        # select all columns
                        for ix in xrange(len(self.columns)):
                            if self.columns[ix] not in res:
                                res.append(self.columns[ix])
                    elif len(sel.dimvalues) == 1:
                        # single column
                        colname = sel.dimvalues[0]
                        if isinstance(colname, int):
                            colname = self.columns[colname]
                        if colname not in res:
                            res.append(colname)
                    else:
                        # start/stop column
                        startcolix = self._convert_to_colnum(sel.dimvalues[0]) or 0
                        stopcolix = self._convert_to_colnum(sel.dimvalues[1]) or len(self.columns)
                        for ix in xrange(startcolix, stopcolix):
                            if self.columns[ix] not in res:
                                res.append(self.columns[ix])
        return res

    def _selectors_to_slices(self, sels):
        res = [ slice(0,self.shape[dim]) for dim in range(len(self.shape)) ]  # start from max ranges
        if sels is not None:
            for sel in sels:
                dim = self._get_dim(sel.dimname)
                if dim >= 0 and dim < len(self.shape):
                    if self.is_dataframe() and dim == 1:
                        # convert the column names to column ids if needed
                        dimvals = [self._convert_to_colnum(dimval) for dimval in sel.dimvalues]
                    elif self.is_table() and dim == 1:
                        # cannot slice table by column (do it later)
                        dimvals = None
                    else:
                        dimvals = sel.dimvalues
                    if dimvals is not None:
                        if len(dimvals) > 1:
                            res[dim] = slice(dimvals[0] or res[dim].start, dimvals[1] or res[dim].stop)
                        elif len(dimvals) == 1 and dimvals[0] is not None:
                            res[dim] = slice(dimvals[0], dimvals[0]+1)
        return tuple(res)
    
    def _get_dim(self, dimname):
        if self.is_dataframe() or self.is_table():
            if dimname in ['row', '__dim1__']:
                return 0
            elif dimname in ['field', '__dim2__']:
                return 1
            else:
                return None
        elif self.is_array():
            if dimname in ['row', '__dim1__']:
                return 0
            else:
                parser = re.compile('__dim(?P<num>[0-9]+)__')
                toks = re.search(parser, dimname)
                if toks is not None:
                    return int(toks.groupdict()['num'])-1
            return None
        else:
            return None
        
    def _convert_to_colnum(self, colname):
        if colname is None or isinstance(colname, int):
            return colname
        for ix in xrange(len(self.columns)):
            if self.columns[ix] == colname:
                return ix
        raise RuntimeError("column %s not found" % colname)
    
    def _gen_dataframe_filter(self, arr, cond):
        if isinstance(cond, OrConditionTuple):
            left_cond = self._gen_dataframe_filter(arr, cond.left)
            right_cond = self._gen_dataframe_filter(arr, cond.right)
            return (left_cond) | (right_cond) if left_cond is not None and right_cond is not None else (left_cond or right_cond)
        elif isinstance(cond, AndConditionTuple):
            left_cond = self._gen_dataframe_filter(arr, cond.left)
            right_cond = self._gen_dataframe_filter(arr, cond.right)
            return (left_cond) & (right_cond) if left_cond is not None and right_cond is not None else (left_cond or right_cond)
        elif isinstance(cond, ConditionTuple):
            left_cond = self._gen_dataframe_filter(arr, cond.left)
            if left_cond is None:
                return None
            # if multiple left_cond, combine via 'OR'
            return reduce(lambda x,y: (x) | (y),
                   [{
                    '=': lambda x,y: (x) == (y),
                    '!=': lambda x,y: (x) != (y),
                    '<': lambda x,y: (x) < (y),
                    '<=': lambda x,y: (x) <= (y),
                    '>': lambda x,y: (x) > (y),
                    '>=': lambda x,y: (x) >= (y)
                    }[cond.comp](single_left_cond, float(cond.right))
                    for single_left_cond in left_cond])
        elif isinstance(cond, CellSelectionTuple):
            cols = self._selectors_to_columns(cond.selectors)
            return [arr[col] for col in cols] if len(cols)>=1 else None
    
    def _gen_table_filter(self, arr, cond):
        if isinstance(cond, OrConditionTuple):
            left_str = self._gen_table_filter(arr, cond.left)
            right_str = self._gen_table_filter(arr, cond.right)
            return "(%s) | (%s)" % (left_str, right_str) if left_str is not None and right_str is not None else (left_str or right_str)
        elif isinstance(cond, AndConditionTuple):
            left_str = self._gen_table_filter(arr, cond.left)
            right_str = self._gen_table_filter(arr, cond.right)
            return "(%s) & (%s)" % (left_str, right_str) if left_str is not None and right_str is not None else (left_str or right_str)
        elif isinstance(cond, ConditionTuple):
            left_str = self._gen_table_filter(arr, cond.left)
            if left_str is None:
                return None
            # if multiple left_cond, combine via 'OR'
            return reduce(lambda x,y: "(%s) | (%s)" % (x,y),
                   ["%s %s %s" % (single_left_str, cond.comp if cond.comp != '=' else '==', float(cond.right))
                   for single_left_str in left_str])
        elif isinstance(cond, CellSelectionTuple):
            cols = self._selectors_to_columns(cond.selectors)
            return cols if len(cols)>=1 else None
    
    def _gen_array_filter(self, arr, slices, cond):
        if isinstance(cond, OrConditionTuple):
            return (self._gen_array_filter(arr, slices, cond.left)) | (self._gen_array_filter(arr, slices, cond.right)) 
        elif isinstance(cond, AndConditionTuple):
            return (self._gen_array_filter(arr, slices, cond.left)) & (self._gen_array_filter(arr, slices, cond.right))
        elif isinstance(cond, ConditionTuple):
            # get the selection slices in the CellSelectionTuple and construct boolean array of size of incoming slices
            # with cells in selection slices set to True, all others set to False
            sel_slices = self._selectors_to_slices(cond.left.selectors)
            mask = self._gen_mask(slices, sel_slices)
            return ({
                     '=': lambda x,y: (x) == (y),
                     '!=': lambda x,y: (x) != (y),
                     '<': lambda x,y: (x) < (y),
                     '<=': lambda x,y: (x) <= (y),
                     '>': lambda x,y: (x) > (y),
                     '>=': lambda x,y: (x) >= (y)
                    }[cond.comp](arr[Ellipsis], float(cond.right))) & mask

    def _gen_mask(self, outer_slices, sel_slices):
        mask = np.zeros([s.stop-s.start for s in outer_slices], dtype=bool)
        mask_slices = self._and_slices(outer_slices, sel_slices)
        mask[[slice(mask_slices[dim].start-outer_slices[dim].start, mask_slices[dim].stop-outer_slices[dim].start) for dim in xrange(len(outer_slices))]] = True
        return mask

#---------------------------------------------------------------------------------------
# Actual query processor operating on abstract tuple language
#---------------------------------------------------------------------------------------

def run_query( arr, sels=None, cond=None, want_cell_coord=False, want_stats=False, keep_dims=None ):
    """
    Input:     ArrayOrTable object to query
               query to run (selection and/or filter condition),
               want coord back (or only values, if False)
               want all stats back
               dims to keep (higher dims use only slice "0" values)
    Output:    DataFrame or numpy array
               dim size list
               offset (row)
               coltype list
               colname list
    """
    if not isinstance(arr, ArrayOrTable):
        arr = ArrayOrTable(arr)
    
    if sels is not None and not isinstance(sels, list):
        sels = [sels]
    
    assert sels is None or all([sel.agg is not None for sel in sels]) or all([sel.agg is None for sel in sels])  # all aggs or all non aggs, cannot mix 
    
    # no coords needed if agg
    if sels is not None and sels[0].agg is not None:
        want_cell_coord = False

    # limit dims
    if sels is not None and keep_dims is not None:
        new_sels = []
        for sel in sels:
            new_selectors = copy.deepcopy(sel.selectors)
            for dim in xrange(keep_dims, len(arr.get_shape())+1):
                if "__dim%s__"%dim not in [ single_sel.dimname for single_sel in sel.selectors ]:
                    new_selectors.append( SelectorTuple( dimname="__dim%s__"%dim, dimvalues=[0] ) )
            new_sels.append(CellSelectionTuple(selectors=new_selectors, agg=sel.agg, alias=sel.alias))
        sels = new_sels

    # push down slicing for both sels and cond
    log.debug("run_query %s sels=%s cond=%s" % (arr, sels, cond))
    slices = arr.get_slices(sels, cond)
    log.debug("slices=%s" % str(slices))
    if slices is None:
        # nothing selected
        data = None
    else:
        # get iterator based on slices & cond
        row_iter = arr.get_slice_iter(slices, cond, want_cell_coord)
    
        # get iterator based on sels
        row_iter = arr.get_sels_iter(row_iter, sels, want_cell_coord)
    
        # format and return result (convert into dataframe or numpy array)
        try:
            peek = row_iter.next()
            if isinstance(peek, np.ndarray):
                data = peek
            else:
                data = pd.DataFrame(data=(x for x in itertools.chain([peek], row_iter)))
        except StopIteration:
            # empty result
            data = None
    
    # set empty to correct type
    if data is None:
        if arr.is_array():
            data = np.empty((), dtype=arr.get_arr().dtype)   # empty array
        else:
            data = pd.DataFrame()                            # empty table
    
    if want_stats:
        # compute all other stats
        dim_sizes = [d for d in data.shape]
        offset = slices[0].start if slices is not None and len(slices)>0 else 0
        if isinstance(data, np.ndarray):
            colnames = [str(i) for i in xrange(slices[1].start, slices[1].stop)] if len(slices)>1 and cond is None else (['0'] if cond is None else ['filtered cells'])
            coltypes = [arr.get_arr().dtype.name] * data.shape[1] if len(data.shape) > 1 else [arr.get_arr().dtype.name]
        else:
            colnames = data.columns.tolist()
            coltypes = [data.dtypes[colname].name for colname in colnames]
        
        return data, dim_sizes, offset, coltypes, colnames
    else:
        return data    
    

#---------------------------------------------------------------------------------------
# Query string parser; generates abstract tuple language query
#---------------------------------------------------------------------------------------

class ParseError(Exception): pass

class TableQueryLexer:
    # constant patterns
    decimal_constant = '((0)|([1-9][0-9]*))'
    exponent_part = r"""([eE][-+]?[0-9]+)"""
    fractional_constant = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
    floating_constant = '((('+fractional_constant+')'+exponent_part+'?)|([0-9]+'+exponent_part+'))'

    keywords = ( 'AND', 'OR', 'AS' )
    tokens = keywords + ('ID', 'LP', 'RP', 'LB', 'RB', 'COLON', 'COMMA', 'STRVAL', 'INTVAL', 'FLOATVAL',
                         'PLUS', 'MINUS', 
                         'LT', 'LE', 'GT', 'GE', 'EQ', 'NE')

    #t_TAGVAL   = r'\w+\*?'
    t_PLUS              = r'\+'
    t_MINUS             = r'-'
    t_LP                = r'\('
    t_RP                = r'\)'
    t_LB                = r'\['
    t_RB                = r'\]'
    t_LE                = r'<='
    t_GE                = r'>='
    t_LT                = r'<'
    t_GT                = r'>'
    t_EQ                = r'='
    t_NE                = r'!='
    t_COLON             = r'[:;]'
    t_COMMA             = r','

    t_ignore = ' \t\n'

    # the following floating and integer constants are defined as
    # functions to impose a strict order

    @TOKEN(floating_constant)
    def t_FLOATVAL(self, t):
        t.value = float(t.value)
        return t

    @TOKEN(decimal_constant)
    def t_INTVAL(self, t):
        t.value = int(t.value)
        return t

    def t_STRVAL(self,t):
        r"(?:'(?:\\'|[^'])*')|(?:\"(?:\\\"|[^\"])*\")"
        t.value = t.value[1:-1].replace(r'\"', r'"').replace(r"\'", r"'")
        return t

    def t_ID(self,t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        if t.value.upper() in self.keywords:
            t.value = t.value.upper()
            t.type = t.value
        else:
            t.value = t.value.lower()
            t.type = 'ID'
        return t
    
    def t_error(self,t):
        raise ParseError( "Illegal character '%s'" % t.value[0] )
        t.lexer.skip(1)

    def __init__(self):
        self.lexer = lex.lex(module=self, optimize=1)

    def tokenize(self,data):
        'Debug method!'
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if tok:
                yield tok
            else:
                break
            
class TableQueryParser:
    # standard precendence rules
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE'),
        ('left', 'GT', 'GE', 'LT', 'LE'),
        ('right', 'UPLUS', 'UMINUS')
    )

    def __init__(self):
        """Create new parser and set up parse tables."""
        self.lexer = TableQueryLexer()
        self.tokens = self.lexer.tokens
        self.cond_parser = yacc.yacc(module=self,write_tables=False,debug=False,optimize=False, start='filter_cond')
        self.slice_parser = yacc.yacc(module=self,write_tables=False,debug=False,optimize=False, start='slice_cond')
    
    def parse_cond(self, query, colnames):
        self.colnames = colnames
        return self.cond_parser.parse(query,lexer=self.lexer.lexer,debug=True)
    
    def parse_slice(self, query, colnames):
        self.colnames = colnames
        return self.slice_parser.parse(query,lexer=self.lexer.lexer,debug=True)
    
    def p_error(self,p):
        if p:
            raise ParseError("Unexpected symbol: '%s'" % p.value)
        else:
            raise ParseError("Unexpected end of query")

    # TODO: retire the first rule (single cell_sel without '[',']') once UI is updated
    def p_slice_cond(self,p):
        '''slice_cond : cell_sel
                      | slice_list
                      | agg_list
        '''
        if len(p[1]) == 0:
            p[0] = []
        elif isinstance(p[1][0], CellSelectionTuple):
            p[0] = p[1]
        else:
            p[0] = [ CellSelectionTuple(selectors=p[1], agg=None, alias=None) ]
        
    def p_slice_list(self,p):
        '''slice_list : slice_list COMMA LB cell_sel RB
                      | LB cell_sel RB
        '''
        if len(p) == 6:
            p[0] = p[1] + [ CellSelectionTuple(selectors=p[4], agg=None, alias=None) ]
        else:
            p[0] = [ CellSelectionTuple(selectors=p[2], agg=None, alias=None) ]
    
    def p_agg_list(self,p):
        '''agg_list : agg_list COMMA ID LP cell_sel RP AS STRVAL
                    | agg_list COMMA ID LP cell_sel RP
                    | ID LP cell_sel RP AS STRVAL
                    | ID LP cell_sel RP
        '''
        if len(p) == 9:
            p[0] = p[1] + [ CellSelectionTuple(selectors=p[5], agg=_check_aggfct(p[3]), alias=p[8]) ]
        elif len(p) == 7:
            if isinstance(p[1], list):
                p[0] = p[1] + [ CellSelectionTuple(selectors=p[5], agg=_check_aggfct(p[3]), alias=None) ]
            else:
                p[0] = [ CellSelectionTuple(selectors=p[3], agg=_check_aggfct(p[1]), alias=p[6]) ]
        else:
            p[0] = [ CellSelectionTuple(selectors=p[3], agg=_check_aggfct(p[1]), alias=None) ]
            
    def p_filter_cond(self,p):
        '''filter_cond : filter_cond OR and_expr
                       | and_expr
        '''
        if len(p) == 4:
            p[0] = OrConditionTuple(left=p[1], right=p[3])
        else:
            p[0] = p[1]
            
    def p_and_expr(self,p):
        '''and_expr : and_expr AND comp_cond
                    | comp_cond
        '''
        if len(p) == 4:
            p[0] = AndConditionTuple(left=p[1], right=p[3])
        else:
            p[0] = p[1]
            
    def p_comp_cond(self,p):
        '''comp_cond : LP filter_cond RP
                     | LB cell_sel RB EQ unary_expr
                     | LB cell_sel RB NE unary_expr
                     | LB cell_sel RB GT unary_expr
                     | LB cell_sel RB GE unary_expr
                     | LB cell_sel RB LT unary_expr
                     | LB cell_sel RB LE unary_expr
        '''
        if len(p) == 4:
            p[0] = p[2]
        else:
            p[0] = ConditionTuple(left=CellSelectionTuple(selectors=p[2], agg=None, alias=None), comp=p[4], right=p[5])
        
    def p_unary_expr(self,p):
        '''unary_expr : MINUS unary_expr %prec UMINUS
                      | PLUS unary_expr %prec UPLUS
                      | INTVAL
                      | FLOATVAL
                      | STRVAL
        '''
        if len(p) == 3:
            p[0] = (p[2] if p[1] == '+' or isinstance(p[2], basestring) else -p[2])
        else:
            p[0] = p[1]
            
    def p_cell_sel(self,p):
        '''cell_sel : cell_sel COMMA single_dim_sel
                    | single_dim_sel
        '''
        if len(p) == 4:
            p[3] = SelectorTuple(dimname=p[3].dimname or '__dim%s__' % (len(p[1])+1), dimvalues=p[3].dimvalues)
            p[0] = p[1] + [ p[3] ]
        else:
            p[1] = SelectorTuple(dimname=p[1].dimname or '__dim1__', dimvalues=p[1].dimvalues)
            p[0] = [ p[1] ]
            
    def p_single_dim_sel(self,p):
        '''single_dim_sel : STRVAL EQ range_sel
                          | range_sel
        '''
        if len(p) == 4:
            p[0] = SelectorTuple(dimname=p[1], dimvalues=p[3])
        else:
            p[0] = SelectorTuple(dimname=None, dimvalues=p[1])
            
    def p_range_sel(self,p):
        '''range_sel : COLON
                     | index_expr
                     | index_expr COLON
                     | COLON index_expr
                     | index_expr COLON index_expr
        '''
        if len(p) == 2:
            p[0] = [None] if p[1] in [':', ';'] else [p[1]]
        elif len(p) == 3:
            if p[2] in [':', ';']:
                p[0] = [p[1],None]
            else:
                p[0] = [None,self._adjust_endcol(p[2])]
        else:
            p[0] = [p[1],self._adjust_endcol(p[3])]
    
    def _adjust_endcol(self, endcol):
        if isinstance(endcol, int):
            endcol += 1
        else:
            endcol = self.colnames.index(endcol)
            endcol += 1
            if endcol >= len(self.colnames):
                endcol = None
            else:
                endcol = self.colnames[endcol]
        return endcol
    
    def p_index_expr(self,p):
        '''index_expr : INTVAL
                      | STRVAL
        '''
        p[0] = p[1]

#---------------------------------------------------------------------------------------
# Table base
#---------------------------------------------------------------------------------------

class TableBase(object):
    '''Formats tables into output format'''

    name = ''
    version = '1.0'
    ext = 'table'
    mime_type = 'text/plain'

    # general functionality defined in the base class

    def __str__(self):
        r = self.resource #etree.tostring(self.resource) if self.resource is not None else 'None'
        m = self.data.shape if self.data is not None else 'None'
        t = type(self.t)
        return 'TableBase(m: %s, t: %s res: %s, path: %s)'%(m, t, r, self.path)

    def isloaded(self):
        """ Returns table information """
        return self.t is not None


    # functions to be defined in the individual drivers

    def __init__(self, uniq, resource, path, **kw):
        """ Returns table information """
        self.path = path
        self.resource = resource
        self.uniq = uniq
        self.url = kw['url'] if 'url' in kw else None

        self.subpath = None # list containing subpath to elements within the resource
        self.tables = None # {'path':.., 'type':..} for all available tables in the resource
        self.t = None # represents a pointer to the actual element being operated on based on the driver
        self.t_cond = None   # filter expression to be performed on t 
        self.t_slice = None  # slice expression to be performed on t
        self.data = None # Numpy array or pandas dataframe
        self.offset = 0
        self.headers = None
        self.types = None
        self.sizes = None

    def close(self):
        """Close table"""
        abort(501, 'Import driver must implement Close method')

    def as_array(self):
        if isinstance(self.data, pd.core.frame.DataFrame):
            return self.data.as_matrix()   # convert to numpy array
        else:
            return self.data

    def as_table(self):
        if isinstance(self.data, pd.core.frame.DataFrame):
            return self.data
        else:
            if self.data.ndim == 1:
                return pd.DataFrame(self.data)
            else:
                raise RuntimeError("cannot convert multi-dim array into dataframe")

    def info(self, **kw):
        """ Returns table information """
        # load headers and types if empty
        return { 'headers': self.headers, 'types': self.types }

    def filter(self, cond):
        """ Filter table with some condition
            Condition syntax:
              FILTER_COND ::=  or_cond  |  "(" or_cond ")"
              or_cond     ::=  and_cond  ( "or" and_cond )*
              and_cond    ::=  comp_cond  ( "and" comp_cond )*
              comp_cond   ::=  "[" cell_sel "]"  ("="|"!="|"<"|">"|"<="|">=")  <value>
              cell_sel    ::=  ( [ <dimname> "=" ] [ <colname> ] [ ":"|";" ] [ <colname> ]  ","  )+
            Example:
              .../filter:[field="temperature"] >= 0 and [field="temperature"] <= 100/... 
              .../filter:[x=0:10, y=0:10, c="infrared", field="r"] > 0.5/...    (x/y/z/c/t will be set for cells with "r > 0.5")  
              .../filter:[0:10,0:10,50,:,"abc"] > 0.5/...                       (no field=> cell has to be numeric, not compound)
        """
        try:
            filtercond = TableQueryParser().parse_cond(cond, self.headers)
        except ParseError as e:
            abort(400, str(e))
        if self.t_slice is not None:
            abort(501, 'Filter condition cannot follow slice operation currently')
        if self.t_cond is None:
            self.t_cond = filtercond
        else:
            self.t_cond = AndConditionTuple(left=self.t_cond, right=filtercond)
        return self

    def slice(self, sel):
        """ Select subset of columns/slices plus aggregation
            Condition syntax:
               PROJ_COND  ::=  cell_sel | agg_cond | agg_cond ( "," agg_cond )+ 
               agg_cond   ::=  agg_fct "(" cell_sel ")" ( "AS" <aliasname> )?
               agg_fct    ::=  "SUM" | "AVG" | "MIN" | "MAX" | ...
            Example:
               .../slice:AVG(row=0:10,field="depth") AS avgdepth, MAX(row=0:10,field="depth") AS maxdepth/...
               .../slice:SUM(0:10,0:10,0:10) AS total/...
               .../slice:0:100,"Ocean_flag"/...
        """
        try:
            slicecond = TableQueryParser().parse_slice(sel, self.headers)
        except ParseError as e:
            abort(400, str(e))
        if self.t_slice is None:
            self.t_slice = slicecond
        else:
            abort(501, 'Only one slice operation allowed currently')
        return self

    def read(self, **kw):
        """ Read table cells and return """
#         if 'rng' in kw and kw.get('rng') is not None:
#             row_range = kw.get('rng')[0]
#             self.offset = row_range[0] or 0 if len(row_range)>0 else 0
#         else:
#             self.offset = 0
        return self.data

    def write(self, data, **kw):
        """ Write cells into a table"""
        abort(501, 'Write not implemented')

    def delete(self, **kw):
        """ Delete cells from a table"""
        abort(501, 'Delete not implemented')
