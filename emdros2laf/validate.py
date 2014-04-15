import sys
import os
import os.path

from .mylib import *

class Validate:
    ''' Validates all generated files, knows the schemas involved.

    The main program generates a bunch of XML files, according to various schemas.
    They can be sent to this object, with or without a schema specification.
    All files with a schema specification will be validated.

    The base locations of the schemas and of the generated files will be retrieved 
    from the main configuration.
    All schemas will be copied from source to destination.

        generated_files = list of [absolute_path, schema in destination, validation result]

    '''

    cfg = None

    generated_files = []

    def __init__(self, cfg):
        ''' Initialization is: get from config the schema locations and copy them all over
        '''

        self.cfg = cfg

        res_dir = cfg.env['decl_dst_dir']
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)

        os.environ[cfg.xml['xmllint_cat_env_var']] = cfg.xml['xmllint_cat_env_val']

        xmlitems = cfg.xml
        errors = 0
        for src_item in xmlitems:
            if src_item.endswith('_src'):
                dst_item = src_item.replace('_src', '_dst')
                if dst_item in xmlitems:
                    cmd = 'cp "{}" "{}"'.format(cfg.xml[src_item], cfg.xml[dst_item])
                    error = runx(cmd)
                    if error:
                        errors += 1
        if errors > 0:
            raise Exception

    def add(self, xml, xsd):
        ''' Add an item to the generated files list. If xsd is given, the file will eventually be validated.

        The validation result will be stored in a member of the item, which is initially None.
        If validation takes place, None will be replaced by True or False, depending on whether
        the xml is valid wrt. the xsd.
        '''
        self.generated_files.append([xml, xsd, None])

    def validate(self):
        ''' Validate all eligible files, but only if the validation flag is on
        '''
        if not self.cfg.flag('validate'):
            return

        for item in self.generated_files:
            absolute_path, schema_dst, is_valid = item
            if schema_dst == None:
                continue
            print("INFO: validating {}".format(absolute_path))
            error = runx(self.cfg.xml['xmllint_cmd'].format(
                schema = schema_dst,
                xmlfile = absolute_path,
            ))
            if not error:
                item[2] = True
            elif error > 0:
                item[2] = False
            else:
                errors += 1

    def report(self):
        ''' Print a list of all generated files and indicate validation outcomes
        '''
        for item in self.generated_files:
            absolute_path, schema_dst, is_valid = fillup(3, None, item)
            message = 'INFO: Generated '
            if schema_dst == None:
                message += '{:<4} file {:<9} {}'.format('text', '', os.path.basename(absolute_path))
            else:
                is_valid_repr = 'UNKNOWN' if is_valid == None else 'VALID' if is_valid else 'NOT VALID'
                message += '{:<4} file {:<9} {:<40} wrt. {}'.format('xml', is_valid_repr, os.path.basename(absolute_path), os.path.basename(schema_dst))
            print(message)
