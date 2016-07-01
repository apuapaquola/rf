#!/usr/bin/env python
""" rf - A framework for collaborative computational research

    Copyright (C) 2015 Apua Paquola <apuapaquola@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
import tempfile
import os
import base64
import subprocess
from argparse import Namespace
import rflib


__author__ = 'Apua Paquola'


class UnitTests(unittest.TestCase):

    def test_run(self):
        """Create dummy analysis tree, run driver scripts and check output"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                print('NAME', __name__)
                cur_dir = os.getcwd()
                os.chdir(tmpdirname)

                with open("dummy.tar.gz", "wb") as f:
                    f.write(base64.b64decode(
                        b'H4sIAFWidVcAA+2Z3WqDQBBGve5TWHof98d17wpN0+coGoXkIk3QpLRv310VKpPQRqqjpN9BIm6ELBx3vh2Tn3a7z' +
                        b'ygYFeGwxviztEbU1zKO63NLIJXVRiuR+PukFEkShGbcaTWcqmNahmGQHk7pz/cVZcUxIV7y2v/bPi+eRnsKrvcvY6' +
                        b'Hc91JJIeGfg67/1804j0Cf9W917T+2MfxzQPzn5fa9KAf+jV/9W9P6d+NCOf/aClf/xcDzuMg/9/9wH2Xbt6ja3BX' +
                        b'rzT5MZfgYVnJx/Di2A8oPqM6A9gO6Hph68uDPfK//l3nlv0H956Drf/r8F8I9Ash/Roj/yfO/8a+ttMh/Dkj+FzT/' +
                        b'C5r/BfL/lqDrvzgMnwFX13/ltv1W+/WvEoX6z8EF//5iNeRv1P6t7eHfuvuDUC0WUXP4KS2Hn5gH/lv/y3nt/7H+W' +
                        b'ej695/PIzwF/f1rlwDwz8G5/+G7wD79nw9+598oDf8cXPQ/cBfYp/9r/Lv2H+9/WSD935r2f2va/63R/90S3fU/h/' +
                        b'd/0srm/R/ynwXif/L3f41/baVB/eeA1P+M1v+M1v8M9f+WoPu/1Vz6P+z/WTj3P23/5466/5P4/5eFi/4n7P8a/67' +
                        b'/E8h/Dkj+5zT/c5r/OfIfAAAAAAAAAAAAAAAAAAAAAAAAAACAufAFz1n1KgBQAAA='))

                subprocess.check_call(['tar', 'xfz', 'dummy.tar.gz'])
                os.chdir('dummy')
                subprocess.check_call(['git', 'init'])
                subprocess.check_call(['git', 'annex', 'init'])

                rflib.run(Namespace(node='.', recursive=True, verbose=True, dry_run=False))

                command = '''export LC_ALL=C; find . -name '*.txt' | sort | md5sum'''
                o = subprocess.check_output(command, shell=True).decode()
                self.assertTrue(o.startswith('2be88994681ecef36d02636683a6bc9e'))

                command = '''export LC_ALL=C; cat `find . -name '*.txt'` | sort | md5sum'''
                o = subprocess.check_output(command, shell=True).decode()
                self.assertTrue(o.startswith('43682754c874d40b3667b2c7c7dc0e65'))

            finally:
                os.chdir(cur_dir)
