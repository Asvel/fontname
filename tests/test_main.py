# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import os
from unittest import TestCase, main

from fontname import guess_font_name


here = os.path.abspath(os.path.dirname(__file__))


class TestMain(TestCase):

    def test_font_name(self):
        count = 0
        for root, dirs, files in os.walk(os.path.join(here, "fonts")):
            for file in files:
                count += 1
                file_path = os.path.join(root, file)
                font_name = guess_font_name(file_path)
                file_name = os.path.splitext(file)[0]
                self.assertEqual(font_name, file_name)
        self.assertTrue(count > 0, "No test data, please put some font files in tests/fonts/")


if __name__ == '__main__':
    main()
