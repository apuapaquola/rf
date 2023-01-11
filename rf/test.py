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
                b'H4sIAAAAAAAAA+2Z22qDQBRFfe5XTOl7nEvGeSs0Tb+jeIP0IRdihPbvO2MCkZPQRqpHSfdCIo6C' +
                b'A/tc9jFFvV5/xdGgSI+zNpyVs7K5VvN5cz4RKe2MNVom4TmlZJJEwg67rSN1dUj3QkTprk5/fq7c' +
                b'Vxwb4qVo9N9si/JlsCi4XX81l9rfV1pJBf05aOv/vhomBG7S38jE2cSHQMh/baWF/hwQ/ff1pv93' +
                b'/Kq/s6f89+tSe/2NVi4Ssv+tXPLP9X96jLOPTVytHsp8tRWpEs+iUrPD5+G0oMOCbi2YsGCahbE3' +
                b'D/7MOf/fptX/Uf9ZaOs/pf6v4P9YIPoX5a7/GLg5/7XzQWCa/p9o6M/BFf3DxbLPdzT6O9dBf+ef' +
                b'j4SezeLjEba06H9jAejf1n90/+8tQJP/RsL/c0D8f0n9f0n9fwn/f0+c838xLf+P/s9CW//w+zpA' +
                b'FHTX3/gOAP05uNS//ymw+/znQwH//7BwVf+eXWAX/xcGP39TW3z/ZYH4v5z6v5z6vxz+755o5/+U' +
                b'vv9J1H8WiP6jz//KqWb+1wnqPwek/me0/me0/meo//cE9X/Lqcx/BvWfg0v9JzL/OejPwVX9R5z/' +
                b'/HGc/xT6Pwek/xe0/xe0/xfo/wAAAAAAAAAAAAAAAAAAAAAAAAAAAEyFb6LrQrMAUAAA'))

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
                self.assertTrue(o.startswith('2be88994681ecef36d02636683a6bc9e'))

                command = '''export LC_ALL=C; cat `find . -name '*.txt'` | sort | md5sum'''
                o = subprocess.check_output(command, shell=True).decode()
                self.assertTrue(o.startswith('43682754c874d40b3667b2c7c7dc0e65'))

            finally:
                os.chdir(cur_dir)

    def test_run_native(self):
        """Runs a test tree natively"""
        self.skel_test_run()

