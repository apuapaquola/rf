#!/usr/bin/env python
""" rf - A minimalist framework for reproducible computation

    Copyright (C) 2015 Apuã Paquola <apuapaquola@gmail.com>

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

    Usage:
    python -m unittest test.py

"""

import unittest
import tempfile
import os
import base64
import subprocess
from argparse import Namespace
import rflib


__author__ = 'Apuã Paquola'


class UnitTests(unittest.TestCase):

    @staticmethod
    def write_dummy_tree_and_init_git():
        """Creates dummy analysis tree and inits the git repo. It cds to 'dummy' """
        with open("dummy.tar.gz", "wb") as f:
            f.write(base64.b64decode(
                b'H4sIAAAAAAAAA+2Zy2rDMBBFve5XuHQfS6NI2hWapt9R/IJ0kQd5QPv3leyWmEloYmrLbnoPJkpk' +
                b'gwVHmhkpxWG5/EiiXhEOq7VvpdWi2X4TSbJKKxLGPyddY6NY9zusmsNun27jOEo3h/Sn5y7d/6MU' +
                b'lf/VuiifepsFV/nXgpQU0hjj/EtjNfyHoOn/Ne9nClzlXwnn3Ggl/fonshL+Q8D8bw+r7t9x0b9b' +
                b'7HX8dzcEOf/ui4pi0f1QTvnn/h/uk+xtlewWd2W+WMepjB/jnZzs3/dfHeQ7qNGhfIeqOoYePPg1' +
                b'x/X/Mqb8bwXifxCa/keV/1H/BYH5L8pN93Pg6v0fWTcJVJX/pwb+Q3DGv/8x7/IdlX9rW/h3WcDV' +
                b'fzSZJPXlhzTrfmAe+G/6H7z+V3JarX/XoP4PAKv/S17/l7z+L1H/3xLH9T8bU/1vLPJ/EJr+/edz' +
                b'D7OgvX+yBP9BOPXf/S6w/f5PKSL4D8FZ/x1XgW3qPzL+/Hcqpjj/DQKr/3Je/+W8/stR/90SfP3P' +
                b'x5L/8f9/EE79jyT/K/gPwVn/A+Z/d1X5X2nk/xCw/F/w/F/w/F8g/98SzfU/qv//sP8LAvM/+Pm/' +
                b'tLI+/yfE/xCw+J/x+J/x+J8h/gMAAAAAAAAAAAAAAAAAAAAAAAAAADAWPgEUSJmxAFAAAA=='))

        subprocess.check_call(['tar', 'xfz', 'dummy.tar.gz'])
        os.chdir('dummy')
        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['git', 'annex', 'init'])

    def skel_test_run(self):
        """Create dummy analysis tree, run driver scripts and check output"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            try:
                print('NAME', __name__)
                cur_dir = os.getcwd()
                os.chdir(tmpdirname)

                self.write_dummy_tree_and_init_git()

                rflib.run(Namespace(node='.', recursive=True, verbose=True, dry_run=False))

                command = '''export LC_ALL=C; find . -name '*.txt' | sort | md5sum'''
                o = subprocess.check_output(command, shell=True).decode()
                self.assertTrue(o.startswith('873a9c2d4a56e62c7afd955057e54ac1'))

                command = '''export LC_ALL=C; cat `find . -name '*.txt'` | sort | md5sum'''
                o = subprocess.check_output(command, shell=True).decode()
                self.assertTrue(o.startswith('43682754c874d40b3667b2c7c7dc0e65'))

            finally:
                os.chdir(cur_dir)

    def test_run_native(self):
        """Runs a test tree natively"""
        self.skel_test_run()

