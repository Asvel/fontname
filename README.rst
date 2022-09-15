========
fontname
========


fontname is a lib for reading and decoding quirk encoded name records from OpenType fonts.

It is adept at dealing with CJK fonts and has been tested on over 10000 fonts.


Installation
------------

``pip install fontname``

fontname requires Python 3.7 and above.


Usage examples
--------------

.. code:: python

    >>> import fontname
    >>> fontname.get_display_names("msyh.ttc")
    '微软雅黑 & Microsoft Yahei UI'

    >>> from fontTools import ttLib
    >>> tt = ttLib.TTFont("MO-UDShinGoSCGb4-Bol.otf")
    >>> fontname.decode_name(tt['name'].names[19])
    ('森泽UD新黑 Gb4 B', <IssueLevel.MARK: 1>, 'x_mac_simp_chinese_ttx')
    >>> tt.close()

    >>> tt = ttLib.TTFont("文鼎粗圆简.TTF")
    >>> fontname.decode_name(tt['name'].names[4])
    ('文鼎粗圆简', <IssueLevel.DATA: 2>, None)
    >>> tt.close()


License
-------

fontname is licensed under the MIT license.
