#!/usr/bin/python
# -*- coding: utf-8 -*-
# ==============================================================================
# title:          utils.py
# description:    Bag of proposed fuctions for main rf package
# author:         Francisco Ivanio
# created_at:     20160705
# updated_at:     20160705
# version:        0.1
# usage:          python utils.py
# test:           python -m doctest -v mytest.py
# python_version: 3
# license:        GPL - http://www.gnu.org/licenses/gpl.html
# ==============================================================================

__author__ = "Francisco Ivanio"
__version__ = "0.1"
__maintainer__ = "Francisco Ivanio"
__email__ = "franciscoivanio@gmail.com"
__status__ = "Development"

import os
import json
import re
import magic
# https://docs.python.org/3/library/configparser.html
from configparser import ConfigParser
import subprocess
import rflib


f = magic.Magic(mime=True, uncompress=True)
MB = 1024*1024.0
DRIVER_PERMISSIONS = [# 0o754, 
                      0o777]  # 0o777 or stat.S_IXUSR see https://docs.python.org/2/library/stat.html


def load_rf_conf(conffile="config.rf"):
    '''
    Load RF vars from file and set as global vars
    '''
    if not os.path.isfile(conffile):
        return False
    config = ConfigParser()
    config.read(conffile)
    global LICENCE
    global AUTHOR
    global PREFIX
    global PROJ_STRUCTURE

    LICENCE = config.get("header_vars", "LICENCE", fallback='')
    AUTHOR = config.get("header_vars", "AUTHOR", fallback='')
    PREFIX = config.get("header_vars", "PREFIX", fallback='')
    PROJ_STRUCTURE = config.get("rf_structure", "PROJ_STRUCTURE", fallback='')

    return True


def createnode(path, driver_template='', create_deps_folder=True):
    '''
    Create rf folders and empty drivers
    '''
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(path + '/_h'):
        os.makedirs(path + '/_h')
    if create_deps_folder and not os.path.exists(path + '/_d'):
        os.makedirs(path + '/_d')
    if not os.path.isfile(path + '/_h/driver'):
        with open(path + '/_h/README', 'w') as readme:
            # get template
            template_r = '''## rf - A framework for collaborative computational research\n```\n
                         pip install git+git://github.com/apuapaquola/rf.git
                         ```\n'''
            print(template_r)
            readme.write(template_r)
        with open(path + '/_h/driver', 'w') as driver:
            # get template
            template_d = "echo 'running driver at %s';\ndate > driver_output;\n" % path
            print(template_d)
            driver.write(template_d)
        for perm in DRIVER_PERMISSIONS:
            os.chmod(path + '/_h/driver', perm)


def subelement(element, structure):
    '''
    Finds a sub element of last node in RF custom structure

    structure={'name': 'first', 'children_node': [], 'index': 0}
    element={'name': 'second', 'children_node': [], 'index': 1}

    to test: python -m doctest -v mytest.py

    >>> element = {'name': 'second', 'children_node': [], 'index': 1}
    >>> structure = {'name': 'first', 'children_node': [], 'index': 0}
    >>> structure = subelement(element, structure)
    >>> json.dumps(structure, sort_keys=True).encode('utf8')
    b'{"children_node": [{"children_node": [], "index": 1, "name": "second"}], "index": 0, "name": "first"}'
    >>> structure = subelement(element, structure)
    >>> element = {'name': 'third', 'children_node': [], 'index': 2}
    >>> structure = subelement(element, structure)
    >>> json.dumps(structure, sort_keys=True).encode('utf8')
    b'{"children_node": [{"children_node": [{"children_node": [], "index": 2, "name": "third"}], \
"index": 1, "name": "second"}, {"children_node": [{"children_node": [], "index": 2, "name": "third"}], \
"index": 1, "name": "second"}], "index": 0, "name": "first"}'
    '''
    if structure['index'] == element['index'] - 1:
        structure['children_node'].append(element)
        return structure
    elif structure['children_node']:
        structure['children_node'][-1] = subelement(element, structure=structure['children_node'][-1])
        return structure
    else:
        return structure


def parse_yaml(proj_struct):
    '''
    Parse yaml project definition
    Returns a dict with the structure
    '''
    pass


def parse_compact(proj_struct_string, json_name=''):
    '''
    Parse custom project definition
    Returns a dict with the structure
    Example:

    mode=compact
    transcriptome
    |alignment
    ||count_reads
    |||DE_method1
    ||||DE_reports
    |||DE_method2
    ||||DE_reports
    ||ann_splicing
    |seq_quality
    '''
    structure = {}

    if proj_struct_string.startswith('mode=compact'):
        max_depth = len(max(re.compile("(\|+\|)").findall(proj_struct_string)))
        print('max depth %d' % max_depth)

        proj_dirs = proj_struct_string.split('\n')[1:]
        dicts = [{'name': i.replace('|', ''), 'index': i.count('|'),
                  'children_node': [], "type": "directory"} for i in proj_dirs]

        roots = [i for i in dicts if i['index'] == 0]
        structure = roots[0]
        for element in dicts:
            # print(structure)
            structure = subelement(element, structure)
            # print(structure)

    if json_name != '':
        with open(json_name, 'w') as outfile:
            json.dump(structure, outfile, sort_keys=True, indent=4, ensure_ascii=False)

    return structure


def create_from_structure(structure, prefix=''):
    '''
    Create rf folders and empty drivers from structure dict
    '''
    if structure["type"] == "directory":
        path = os.path.join(prefix, structure['name'])
        print(path)
        createnode(path)
        if structure['children_node']:
            for s in structure['children_node']:
                create_from_structure(s, prefix=path)


def add_structure_to_git(structure, prefix=''):
    '''
    Add rf folders to git
    '''
    if structure["type"] == "directory":
        path = os.path.join(prefix, structure['name'])
        print(path)
        if os.path.exists(path):
            if os.path.exists(path + '/_h'):
                subprocess.check_call(['git', 'add', '%s/_h' % path])
            if os.path.exists(path + '/_d'):
                subprocess.check_call(['git', 'annex', 'add', '%s/_d' % path])
            if os.path.exists(path + '/_m'):
                subprocess.check_call(['git', 'annex', 'add', '%s/_m' % path])
            if structure['children_node']:
                for s in structure['children_node']:
                    add_structure_to_git(s, prefix=path)


def start_rf_proj():
    '''
    Create rf folders from templates
    Template can be:
    - zip folder
    - PROJ_STRUCTURE (variable on conf)

    $ rf start project
    '''
    load_rf_conf(conffile="config.rf")
    # print(LICENCE, AUTHOR, DRIVER_EXTENSIONS, PROJ_STRUCTURE)
    structure = parse_compact(proj_struct_string=PROJ_STRUCTURE)
    # print(structure)
    print(structure['name'])

    prefix = PREFIX

    base_path = prefix + structure['name']

    create_from_structure(structure, prefix=prefix)

    os.chdir(base_path)
    # INIT
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'annex', 'init'])
    subprocess.check_call(['git', 'annex', 'sync'])
    # ADD to git
    add_structure_to_git(structure, prefix=prefix)
    # COMMIT
    message = 'First commit'

    # branch = 'my_branch'
    PIPE = subprocess.PIPE
    process = subprocess.Popen(['git', 'commit', '-m', message], stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = process.communicate()

    if 'fatal' in stdoutput.decode('UTF-8'):
        # Handle error case
        print(stderroutput.decode('UTF-8'))
        # import pdb; pdb.set_trace()
    else:
        # Success!
        print(stdoutput.decode('UTF-8'))

    return structure


def parse_dir_structure(path, json_name='', parse_files=False):
    '''
    Read and check a RF folder structure from dir
    Returns a dict with the structure
    '''
    ignore = ['.git']

    structure = {'name': os.path.basename(path), 'type': "ignore"}

    if structure['name'] not in ignore:
        if os.path.isdir(path):
            structure['type'] = "directory"
            structure['children_node'] = [parse_dir_structure(os.path.join(path, x)) for x in os.listdir(path)]
            if structure['name'] not in ['_h', '_m', '_d']:
                structure['has_h'] = os.path.isdir(path + '/_h')
                structure['has_m'] = os.path.isdir(path + '/_m')
                structure['has_deps'] = os.path.isdir(path + '/_d')
                structure['has_driver'] = os.path.exists(path + '/_h/driver')
        elif parse_files:
            structure['type'] = f.from_file(path).decode('UTF-8')
            structure['is_driver'] = structure['name'] == 'driver'
            structure['size'] = "%.2f MB" % (os.path.getsize(path)/MB)
            structure['exec'] = os.access(path, os.X_OK)

    # clear sctructure:
    if 'children_node' in structure:
        structure['children_node'][:] = [x for x in structure['children_node'] if x['type'] != "ignore"]

    if json_name != '':
        with open(json_name, 'w') as outfile:
            json.dump(structure, outfile, sort_keys=True, indent=4, ensure_ascii=False)

    return structure


def check_structure(structure, prefix='', print_message=False, archive_message=True, json_name=''):
    '''
    Check rf config and folders

    Possible status:
    - Not verified
    - Directory not found
    - Driver not found
    - Empty driver
    - No permission to execute driver
    - Ready to run
    - Dependecies not satisfied
    - Fail in last run (check logs)
    - Done

    Warnings:
    - Out of version manager
    - Empty README

    # Check links for outside
    # Check broken links
    # make -k keep going
    '''

    possible_status = {'NV': 'Not verified',  # warning
                       'PNF': 'Directory not found',  # warning
                       'DNF': 'Driver not found',  # warning
                       'ED': 'Empty driver',  # warning
                       'NX': 'No permission to execute driver',  # erro
                       'R': 'Ready to run',  # mensagem
                       # 'D': 'Dependecies not satisfied',
                       'F': 'Fail in last run (check logs)',
                       'D': 'Done',
                       }

    if structure['name'] in ['_h', '_m', '_d']:
        return structure

    structure['status_code'] = 'NV'

    if structure["type"] == "directory":
        path = os.path.join(prefix, structure['name'])
        # print(path)
        if os.path.exists(path):
            if os.path.exists(path + '/_m'):
                # improve: check nohup log
                structure['status_code'] = 'D'
            else:
                if os.path.exists(path + '/_h/driver'):
                    if os.stat(path + '/_h/driver').st_size == 0:
                        structure['status_code'] = 'ED'
                    elif not os.access(path + '/_h/driver', os.X_OK):
                        structure['status_code'] = 'NX'
                    elif os.path.exists('/_h/nohup.out'):
                        # improve: check nohup log
                        structure['status_code'] = 'F'
                    else:
                        structure['status_code'] = 'R'
                else:
                    structure['status_code'] = 'DNF'
            if 'children_node' in structure:
                structure['children_node'] = [check_structure(s, prefix=path, print_message=print_message) \
                                              for s in structure['children_node']]
        else:
            structure['status_code'] = 'PNF'

    if archive_message:
        structure['status'] = possible_status[structure['status_code']]

    if print_message:
        print('%s : %s' % (os.path.realpath(path), possible_status[structure['status_code']]))

    if json_name != '':
        with open(json_name, 'w') as outfile:
            json.dump(structure, outfile, sort_keys=True, indent=4, ensure_ascii=False)

    return structure


if __name__ == '__main__':
    # structure = start_rf_proj()
    load_rf_conf(conffile="config.rf")
    prefix = PREFIX
    # base_path = prefix + structure['name']
    base_path = prefix + 'transcriptome'

    structure = parse_dir_structure(base_path, json_name='tests.json')

    # print(structure)
    structure = check_structure(structure, prefix=prefix, print_message=True)

    # mf = rflib.makefile([], rflib.rule_string_native)

    # print(mf)

    '''
    %s: %s
    \tdate
    \tmkdir %s/_m
    \tcd %s/_m
    \t%s/_h/driver > nohup.out 2>&1
    \tdate
    '''

    # structure = parse_dir_structure('../dummy', json_name='tests.json')
    # print(structure)
    # create_from_structure(structure, prefix='')
