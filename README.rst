========
fontname
========


Overview
--------

fontname is a lib for guessing font name, in other words, reading and decoding quirk encoded raw font name.

It current supports `SFNT <http://en.wikipedia.org/wiki/SFNT>`_ format fonts, and is adept at dealing with CJK fonts.

It has been tested with hundreds fonts, but there will be many fonts still not supported, bug report is welcomed.


Installation
------------

``pip install fontname``

fontname require `freetype-py <https://github.com/rougier/freetype-py>`_, it will be installed automatic.


Usage example
-------------

.. code:: python

    from fontname import guess_font_name
    name = guess_font_name("FZZhunYuan-M02.ttf")
    assert name == "方正准圆_GBK"


License
-------

fontname is release under MIT license
