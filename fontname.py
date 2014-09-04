# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals

import logging
import re

import freetype

__version__ = '0.2.0'

logger = logging.getLogger(__name__)


# Preferred(most possible) encoding of SFNT name
# [name.platform_id][name.encoding_id]
sfnt_name_encoding = {
    0: {
        0: 'utf_16_be',
        1: 'utf_16_be',
        2: 'utf_16_be',
        3: 'utf_16_be',
        4: 'utf_16_be',
        5: 'utf_16_be',
    },
    1: {
        0: 'mac_roman',
        1: 'shift_jis',
        2: 'big5',
        3: 'euc_kr',
        4: 'iso8859_6',
        5: 'iso8859_8',
        6: 'mac_greek',
        7: 'iso8859_5',
        8: 'ascii',
        9: 'ascii',
        10: 'ascii',
        11: 'ascii',
        12: 'ascii',
        13: 'ascii',
        14: 'ascii',
        15: 'ascii',
        16: 'ascii',
        17: 'ascii',
        18: 'ascii',
        19: 'ascii',
        20: 'ascii',
        21: 'cp874',
        22: 'ascii',
        23: 'ascii',
        24: 'ascii',
        25: 'euc_cn',
        26: 'ascii',
        27: 'ascii',
        28: 'ascii',
        29: 'ascii',
        30: 'cp1258',
        31: 'ascii',
        32: 'ascii',
    },
    2: {
        0: 'ascii',
        1: 'utf_16_be',
        2: 'latin_1',
    },
    3: {
        0: 'utf_16_be',
        1: 'utf_16_be',
        2: 'shift_jis',
        3: 'gb2312',
        4: 'big5',
        5: 'cp949',
        6: 'johab',
        10: 'utf_32_be',
    },
    4: {
        0: 'ascii',
    },
    7: {
        0: 'utf_16_be',
        1: 'utf_16_be',
        2: 'utf_16_be',
        3: 'utf_16_be',
    },
}

# Default priority of SFNT names
# (language_id, platform_id, encoding_id)
sfnt_name_priority = [
    # zh-Hans
    (2052, 3, 3),
    (2052, 3, 1),
    (33, 1, 25),
    # zh-Hant
    (1028, 3, 4),
    (1028, 3, 1),
    (19, 1, 2),
    # jp
    (1041, 3, 2),
    (1041, 3, 1),
    (11, 1, 1),
    # kr
    (1042, 3, 5),
    (1042, 3, 1),
    (2066, 3, 6),
    (2066, 3, 1),
    (23, 1, 3),
    # en-US
    (1033, 3, 1),
]


def guess_sfnt_name(face, priority=sfnt_name_priority):
    """Guess name from SFNT of a font face

    `priority` is a list of tuples, each tuple contains three item
    (language_id, platform_id, encoding_id), the first matched SFNT
    name will be returned. If `priority` is `None` or `False`, all
    SFNT name objects will be returned.
    """

    # Get raw SFNT names
    names = [face.get_sfnt_name(i) for i in range(face.sfnt_name_count)]
    names = [name for name in names if name.name_id == 4]  # 4 = FULL_NAME
    if not names:
        logger.warning("Can't find a FULL_NAME item in SFNT table")
        return ""

    # Try to decode them
    for name in names:
        raw = name.string
        logger.debug("Process SFNT name (%d, %d, %d) %s",
                     name.language_id, name.platform_id, name.encoding_id, raw)
        try:  # SFNT info preferred encoding
            try:
                encoding = sfnt_name_encoding[name.platform_id][name.encoding_id]
            except KeyError:
                encoding = 'utf_16_be'
            logger.debug("Try encoding %s", encoding)
            s = raw.decode(encoding)
            if "\x00" in s.strip("\x00"):
                raise UnicodeError()
        except UnicodeError:
            try:  # SFNT info preferred encoding with padding \x00
                if re.match(br'^\x00[\x00-\xFF]*$', raw):
                    logger.debug("Try encoding %s after remove padding \\x00", encoding)
                    s = raw.replace(b'\x00', b'').decode(encoding)
                else:
                    raise UnicodeError()
            except UnicodeError:
                try:  # UTF-16 BE
                    encoding = 'utf_16_be'
                    logger.debug("Try encoding %s", encoding)
                    s = raw.decode(encoding)
                except UnicodeError:
                    try:  # ASCII
                        encoding = 'ascii'
                        logger.debug("Try encoding %s", encoding)
                        s = raw.decode(encoding)
                    except UnicodeError:  # failed
                        encoding = None
                        s = ""
        name.encoding = encoding
        name.unicode = s.strip("\x00")
        if name.unicode:
            logger.debug("Success decoded to '%s'", name.unicode)
        else:
            logger.warning("Failed to decode %s".format(name.string))

    # Choose a prefered name if need
    if priority not in (None, False):
        namedict = {(n.language_id, n.platform_id, n.encoding_id): n.unicode for n in names}
        for meta in priority:
            name = namedict.get(meta)
            if name:
                logger.debug("Choose preferred name '%s' with meta %s", name, meta)
                break
        else:
            name = names[-1].unicode
            logger.warning("Can't find any preferred name, choose '%s'", name)
        return name
    else:
        return names


def guess_font_name(filename, join=" & "):
    """Guess name of a font file

    A font file may have multiple faces, name of each face will be
    guessed and joined by the argument `join`, unless `join` is `None`
    or `False`, in this case a list of names will be returned.
    """
    logger.debug("File %s", filename)

    faces = [freetype.Face(filename)]
    faces.extend(freetype.Face(filename, i) for i in range(1, faces[0].num_faces))
    logger.debug("Found %d faces", len(faces))

    names = []
    for index, face in enumerate(faces):
        logger.debug("Process Face %d", index)
        name = ""
        if face.sfnt_name_count > 0:
            logger.debug("Try guess SFNT name")
            name = guess_sfnt_name(face)
        if not name:
            try:
                logger.debug("Try use family name")
                name = face.family_name.decode('ascii')
            except UnicodeDecodeError:
                try:
                    logger.debug("Try use PostScript name")
                    name = face.postscript_name.decode('ascii')
                except UnicodeDecodeError:
                    pass
        if name:
            logger.debug("Got name %s", name)
            if name not in names:
                names.append(name)
        else:
            logger.error("Can't get name of face %d in file %s", index, filename)

    logger.debug("Got font names %s", names)
    if join not in (None, False):
        names = join.join(names)
    return names
