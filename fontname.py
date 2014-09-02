# -*- coding: utf-8 -*-

import re
import logging

import freetype

# SFNT 名称表中平台 ID 和语言 ID 可能对应的编码方式
# sfnt_info_encoding[name.platform_id][name.encoding_id]
sfnt_info_encoding = {
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

# 不同SFNT信息选择的优先级
# (language_id, name.platform_id, name.encoding_id)
sfnt_info_priority = [
    (2052, 3, 3),
    (2052, 3, 1),
    (33, 1, 25),
    (1028, 3, 4),
    (1028, 3, 1),
    (19, 1, 2),
    (1041, 3, 2),
    (1041, 3, 1),
    (11, 1, 1),
    (1042, 3, 5),
    (1042, 3, 1),
    (2066, 3, 6),
    (2066, 3, 1),
    (23, 1, 3),
    (1033, 3, 1),
]


def guess_sfnt_name(face, autochoose=True):
    """猜测带有 SFNT 名称表的字体的字体名称

    face 字体
    autochoose 自动从结果集里选择一个结果，根据 sfnt_info_priority
    返回值 当 autochoose 为 False 时返回字体名称集，否则返回一个字体名称
    """

    # 获取原始字体名称
    names = [face.get_sfnt_name(i) for i in range(face.sfnt_name_count)]
    names = [x for x in names if x.name_id == 4]

    # 猜测字体名称的编码并尝试解码
    for name in names:
        try:
            encoding = sfnt_info_encoding[name.platform_id][name.encoding_id]
        except KeyError:
            encoding = 'utf_16_be'
        try:
            s = name.string.decode(encoding)
            if "\x00" in s.strip("\x00"):
                raise UnicodeDecodeError()
        except UnicodeDecodeError:
            try:
                if re.match(br'^\x00[\x00-\xFF]*$', name.string):
                    s = name.string.replace(b'\x00', b'').decode(encoding)
                else:
                    raise UnicodeDecodeError()
            except UnicodeDecodeError:
                try:
                    encoding = 'utf_16_be'
                    s = name.string.decode(encoding)
                except UnicodeDecodeError:
                    try:
                        encoding = 'ascii'
                        s = name.string.decode(encoding)
                    except UnicodeDecodeError:
                        encoding = None
                        s = ""
        name.encoding = encoding
        name.unicode = s.strip("\x00")
        if name.unicode == "":
            logging.warning("\t无法解码字体名称".format(name.string))
        logging.debug("\t{0.platform_id} {0.encoding_id:>2} {0.language_id:>4}"
                      " {0.encoding:<10} {0.unicode:<80} {0.string}".format(name))

    # (猜测合适的字体名称并)返回字体名称
    if autochoose:
        namedict = {(x.language_id, x.platform_id, x.encoding_id): x.unicode for x in names}
        for info in sfnt_info_priority:
            if info in namedict:
                return namedict[info]
        if len(names) > 0:
            return names[-1].unicode
        else:
            logging.warning("没有从SFNT表中取得字体名称")
            return ""
    else:
        return {x.unicode for x in names}


def guess_names(fontfilename):
    """猜测字体文件中所有字体的首选名称

    fontfilename 字体文件路径
    返回 返回猜测得到的字体名称列表
    """
    names = []
    try:
        faces = [freetype.Face(fontfilename)]
        faces += [freetype.Face(fontfilename, i) for i in range(1, faces[0].num_faces)]
    except freetype.ft_errors.FT_Exception as e:
        faces = []
        logging.error("无法载入文件 {} - {}".format(fontfilename, e))
    for face in faces:
        name = ""
        if face.sfnt_name_count > 0:
            name = guess_sfnt_name(face, True)
        if name == "":
            try:
                name = face.family_name.decode('ascii')
            except UnicodeDecodeError:
                name = ""
        if name == "":
            try:
                name = face.postscript_name.decode('ascii')
            except UnicodeDecodeError:
                name = ""
        if name != "":
            if name not in names:
                names.append(name)
        else:
            logging.error("无法获取字体文件 {} 中某一字体的名称".format(
                fontfilename))
        logging.debug("\t\t{}".format(name))
    return names
