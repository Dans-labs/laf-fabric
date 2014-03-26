import sys
import collections
from .settings import Settings

class Names(Settings):
    '''Manage the names of compiled LAF data items.

    Data items are stored in a dictionary with keys that tell a lot about the kind of data stored under that key.
    Keys have the following format::

        origin group kind direction ( item )

    and **item** is a comma separated list of a variable number of components, possibly zero.

    **Group**:

    * ``P``: primary data items,
    * ``G``: items for regions, nodes, edges, 
    * ``X``: xml identifiers,
    * ``F``: features,
    * ``C``: connectivity,
    * ``T``: temporary during compiling.

    **Origin**: ``m`` or ``a`` meaning *main* and *annox* resp. Indicates the source data.
    The value ``z`` indicates that this data is not prepared by Laf-Fabric but by auxiliary modules.

    **Kind**: ``n`` or ``e`` meaning *node* and *edge* resp.

    **Direction**: ``f`` or ``b`` meaning *forward* and *backward* resp.

    The direction can mean the direction in which edges are followed, or the direction in which a mapping goes.

    **Components**:

    Features are items, with three components: (*namespace*, *label*, *name*).

    In group ``P``, ``G``, ``T`` there are one-component items, such as (``edges_from``,) and (``edges_to``).

    In group ``X`` there is only one item, and it has no components: ().

    For each data item we have to know the conditions under which it has to be loaded and its data type.

    The **condition** is a key in a dictionary of conditions.
    The loader determines the condition dictionary by filling in its slots with relevant components.
    
    The **data type** is either array, or dict, or string.

    **Class methods**
    The class methods ``comp`` and ``decomp`` and ``decompfull`` take care of the composition and decomposition of keys in meaningful bits.

    **Instance data and methods**
    The instance data contains a list of datakeys, adapted to the present environment, which is based
    on the source, annox and task chosen by the user.
    The previous list is also remembered, so that the loader can load/unload the difference.

    The instance method ``request_files`` determines the difference between previously and presently requested data items.
    It uses an instance method ``dinfo`` that provides all relevant information associated with a datakey,
    including the location and name of the corresponding data file on disk. This method is an instance method because it 
    needs values from the current environment.
    '''
    _data_items_tpl = (( 
        ('mP00 node_anchor',       (False, 'arr')),
        ('mP00 node_anchor_items', (False, 'arr')),
        ('mG00 node_anchor_min',   (True,  'arr')),
        ('mG00 node_anchor_max',   (True,  'arr')),
        ('mP00 node_events',       (False, 'arr')),
        ('mP00 node_events_items', (False, 'arr')),
        ('mP00 node_events_k',     (False, 'arr')),
        ('mP00 node_events_n',     (False, 'arr')),
        ('mG00 node_sort',         (True,  'arr')),
        ('mG00 node_sort_inv',     (True,  'dct')),
        ('mG00 edges_from',        (True,  'arr')),
        ('mG00 edges_to',          (True,  'arr')),
        ('mP00 primary_data',      (False, 'str')),
        ('mXnf',                   ([],    'dct')),
        ('mXef',                   ([],    'dct')),
        ('mXnb',                   ([],    'dct')),
        ('mXeb',                   ([],    'dct')),
        ('mFn0',                   ([],    'dct')),
        ('mFe0',                   ([],    'dct')),
        ('mC0f',                   ([],    'dct')),
        ('mC0b',                   ([],    'dct')),
        ('aFn0',                   ([],    'dct')),
        ('aFe0',                   ([],    'dct')),
        ('aC0f',                   ([],    'dct')),
        ('aC0b',                   ([],    'dct')),
        ('zG00 node_sort',         (None,  'arr')),
        ('zG00 node_sort_inv',     (None,  'dct')),
    ))
    _data_items_def = collections.OrderedDict()

    E_ANNOT_YES = ('laf','','y')
    E_ANNOT_NON = ('laf','','x')
    DCOMP_SEP = ','

    load_dict_keys = {'features', 'xmlids', 'primary', 'prepare'}
    load_dict_subkeys = {'node', 'edge'}
    kind_types = {False, True}

    def __init__(self, work_dir, laf_dir, save, verbose):
        Settings.__init__(self, work_dir, laf_dir, save, verbose)
        self.req_data_items = collections.OrderedDict()
        self._old_data_items = collections.OrderedDict()
        for ((dkey_raw, dbits)) in Names._data_items_tpl:
            parts = dkey_raw.split(' ')
            dkey = '{}({})'.format(parts[0], Names.DCOMP_SEP.join(parts[1:])) if len(parts) > 1 else dkey_raw
            Names._data_items_def[dkey] = dbits

    def comp(dkeymin, dcomps): return '{}({})'.format(dkeymin, Names.DCOMP_SEP.join(dcomps))
    def comp_file(dgroup, dkind, ddir, dcomps):
        return'{}{}{}({})'.format(dgroup, dkind, ddir, Names.DCOMP_SEP.join(dcomps))

    def decomp(dkey):
        parts = dkey.split('(', 1)
        return (parts[0], '({}'.format(parts[1])) if len(parts) == 2 else (dkey, '')

    def decomp_full(dkey):
        parts = dkey.split('(')
        return tuple(parts[0]) + (tuple(parts[1].rstrip(')').split(Names.DCOMP_SEP)),)
        
    def apiname(dcomps): return "_".join(dcomps)
    def orig_key(dkey): return dkey.replace('z', 'm', 1) if dkey.startswith('z') else dkey

    def query(dorigin=None, dgroup=None):
        def test(dkey): return (not dorigin or dorigin == dkey[0]) and (not dgroup or dgroup == dkey[1])
        return [dkey for dkey in Names._data_items_def if test(dkey)]

    def deliver(computed_data, dest, data_items):
        if computed_data: data_items[Names.comp(*dest)] = computed_data

    def dmsg(dkey):
        (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
        return '{}: {}{}{}{}'.format(
            'main' if dorigin == 'm' else 'annox' if dorigin == 'a' else 'prep',
            dgroup,
            '.' + Names.apiname(dcomps) if len(dcomps) else '',
            ' [' + ('node' if dkind == 'n' else 'e') + '] ' if dkind != '0' else '',
            ' ' + ('->' if ddir == 'f' else '<-') + ' ' if ddir != '0' else '',
        )

    def request_init(self, req_items):
        req_items.clear()
        for dkey in Names._data_items_def:
            (docc_def, dtype) = Names._data_items_def[dkey]
            docc = Names.decomp(dkey)[0]
            req_items[docc] = docc_def.copy() if type(docc_def) == list or type(docc_def) == dict else docc_def

    def request_files(self, req_items):
        self._old_data_items = self.req_data_items
        self.req_data_items = collections.OrderedDict()
        for dkey in Names._data_items_def:
            (docc_def, dtype) = Names._data_items_def[dkey]
            docc = Names.decomp(dkey)[0]
            if docc not in req_items: continue
            if req_items[docc] == True:
                self.req_data_items[dkey] = self.dinfo(dkey)
            elif req_items[docc] == False or req_items[docc] == None: continue
            else:
                for dcomps in req_items[docc]:
                    dkeyfull = Names.comp(dkey, dcomps)
                    self.req_data_items[dkeyfull] = self.dinfo(dkeyfull)
        dkeys = {'clear': [], 'keep': [], 'load': []}
        old_data_items = self._old_data_items
        new_data_items = self.req_data_items
        for dkey in old_data_items:
            if dkey not in new_data_items or new_data_items[dkey] != old_data_items[dkey]: dkeys['clear'].append(dkey)
        for dkey in new_data_items:
            if dkey in old_data_items and new_data_items[dkey] == old_data_items[dkey]: dkeys['keep'].append(dkey)
            else:
                if not new_data_items[dkey][-1]: dkeys['load'].append(dkey)
        return dkeys

    def dinfo(self, dkey):
        if dkey in Names._data_items_def: (docc_def, dtype) = Names._data_items_def[dkey]
        else:
            dkeymin = Names.decomp(dkey)[0]
            (docc_def, dtype) = Names._data_items_def[dkeymin]
        (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
        if dgroup == 'T': return (None, None, None, None, None)
        dloc = self.env['{}_compiled_dir'.format(dorigin)]
        dfile = Names.comp_file(dgroup, dkind, ddir, dcomps)
        return (dgroup not in 'FC', dloc, dfile, dtype, dorigin == 'z')

    def check_load_dict(load_dict, stamp):
        errors = []
        for key in load_dict:
            if key not in Names.load_dict_keys:
                errors.append('only these keys are allowed: {}, not {}'.format(Names.load_dict_keys, key))
            elif key == 'xmlids':
                for subkey in load_dict[key]:
                    if subkey not in Names.load_dict_subkeys:
                        errors.append('under {} only these keys are allowed: {}, not {}'.format(key, Names.load_dict_subkeys, subkey))
                    else:
                        val = load_dict[key][subkey]
                        if val not in {False, True}:
                            errors.append('under {} and then {} only these values are allowed: {}, not {}'.format(key, subkey, Names.kind_types, val))
            elif key == 'primary':
                val = load_dict[key]
                if val not in {False, True}:
                    errors.append('under {} only these values are allowed: {}, not {}'.format(key, Names.kind_types, val))
            elif key == 'features':
                for namespace in load_dict[key]:
                    for subkey in load_dict[key][namespace]:
                        if subkey not in Names.load_dict_subkeys:
                            errors.append('under {} and then {} only these keys are allowed: {}, not {}'.format(key, namespace, Names.load_dict_subkeys, subkey))
                        else:
                            val = load_dict[key][namespace][subkey]
                            if type(val) != list:
                                errors.append('under {} and then {} and then {} the value should be a list, not {}'.format(key, namespace, subkey, type(val)))
            elif key == 'prepare':
                val = load_dict[key]
                if type(val) != collections.OrderedDict:
                    errors.append('the value of {} should be a collections.OrderedDict, not {}'.format(key, type(val)))
        if errors:
            raise FabricError("Your load instructions have the following errors:\n{}".format('\n'.join(errors)), stamp, None)


class FabricError(Exception):
    def __init__(self, message, stamp, cause=None):
        Exception.__init__(self, message)
        stamp.Emsg(message)
        if cause: stamp.Dmsg("{}: {}".format(type(cause), str(cause)))
