"""Read and decode quirk encoded name records from OpenType fonts."""

import os
from enum import Enum
from fontTools import ttLib

__version__ = '1.0.0'


class IssueLevel(Enum):
    NONE = 0  # everything is ok
    MARK = 1  # encoding mark does not match string data
    DATA = 2  # string data has some problems, it cannot decode with any OpenType supported encoding


def decode_name(name_record):
    """Decode a fonttools NameRecord, return (decoded string, issue level, actual encoding if no data issue)"""
    raw = name_record.string
    encoding = name_record.getEncoding()

    # some names are truncated and data is permanently lost, we can only recover the remaining part (eg: 文鼎勘亭流)
    def decode(encoding_):
        try:
            return raw.decode(encoding_), IssueLevel.NONE if encoding_ == encoding else IssueLevel.MARK, encoding_
        except UnicodeDecodeError as ex:
            if ex.start >= len(raw) - 2:
                return raw.decode(encoding_, 'ignore'), IssueLevel.DATA, None
            else:
                raise ex

    # no such case, but if encountered things will break
    if encoding is None:
        return decode('utf_16_be')

    # empty is empty
    if len(raw) == 0:
        return decode(encoding)

    # among all OpenType supported encoding, only <utf_16_be> may contains '\x00' inside
    # if a '\x00' found, it might..
    if encoding != 'utf_16_be' and b'\x00' in raw.rstrip(b'\x00'):
        # ..prepend a redundant 0x00 before every encoded bytes (eg: 微软简中圆)
        if encoding != 'utf_16_be' and all(b == 0 for b in raw[0::2]):
            try:
                return raw[1::2].decode(encoding), IssueLevel.DATA, None
            except UnicodeDecodeError: pass
        # ..or mistakenly mark <utf_16_be> as other encoding (eg: HG半古印体)
        else:
            try:
                return decode('utf_16_be')
            except UnicodeDecodeError: pass

    # mistakenly mark <shift_jis>/<big5> as <mac_roman>
    # <mac_roman> won't fail on any input, so we must catch this first
    if encoding == 'mac_roman' and len([b for b in raw if b > 0x7f]) > 3:
        # try big5 fisrt as it more likely to fail
        try:
            return decode('x_mac_trad_chinese_ttx')  # (eg: 華康布丁體(P))
        except UnicodeDecodeError: pass
        try:
            return decode('x_mac_japanese_ttx')  # (eg: EPSON 丸ゴシック体Ｍ)
        except UnicodeDecodeError: pass

    # 「恅隋怪，爬——」, the infamous "恅隋xxxx" series (eg: 文鼎粗圆简 = 恅隋棉埴潠翷)
    # they decode some "original" strings with incorrect encoding and re-encode to <utf_16_be>
    # and in some cases, there would be a redundant character at the end
    if encoding == 'utf_16_be' and raw.startswith(b'\x60\x45\x96\x8b'):
        try:
            decoded = raw.decode('utf_16_be').encode('big5').decode('gb2312', 'replace')
            return decoded[:-2] if decoded[-2] == '�' else decoded, IssueLevel.DATA, None
        except UnicodeError: pass

    # mistakenly mark some other encodings as <utf_16_be>
    # it's hard to tell a encoding from <utf_16_be> accurately, we have to match verdor prefixes individually
    if encoding == 'utf_16_be':
        if raw.startswith(b'\xbb\xaa\xbf\xb5'):  # (eg: 华康楷体W5-A)
            try:
                return decode('gb2312')
            except UnicodeDecodeError: pass
        if raw.startswith(b'\xb5\xd8\xb1\x64'):  # (eg: 華康中黑體(P)-UN)
            try:
                return decode('big5')
            except UnicodeDecodeError: pass
        if raw.startswith(b'HanDing'):  # (eg: 汉鼎简中楷)
            try:
                return decode('ascii')
            except UnicodeDecodeError: pass

    # mistakenly mark <x_mac_simp_chinese_ttx> as <x_mac_japanese_ttx> (eg: 森泽UD新黑 Gb4 DB)
    # these two encodings are also hard to distinguish
    if encoding == 'x_mac_japanese_ttx' and raw.startswith(b'\xc9\xad\xd4\xf3'):
        try:
            return decode('x_mac_simp_chinese_ttx')
        except UnicodeDecodeError: pass

    # mistakenly mark <utf_16_be> as some other encodings  (eg: 麗流隷書)
    # usually this fails on decoding with marked encoding, but in rarely case it won't
    # non-unicode encoding only supports a small set of characters, and use very different code points from unicode
    # if the actual encoding is not <utf_16_be>, decoding with it is unlikely to produce a marked encoding encodable content
    # skip truncation detection for mininal false positives
    if encoding != 'utf_16_be' and len(raw) % 2 == 0:
        try:
            decoded = raw.decode('utf_16_be')
            decoded.encode(encoding)
            return decoded, IssueLevel.MARK, 'utf_16_be'
        except UnicodeError: pass

    # try fonttools' decoder
    try:
        decoded = name_record.toUnicode()
        if decoded == raw.decode(encoding, 'replace'):
            return decoded, IssueLevel.NONE, encoding
        else:
            return decoded, IssueLevel.DATA, None
    except UnicodeDecodeError: pass

    # mark as 'x_mac_simp_chinese_ttx', but use an extend edition actually (eg: 方正字迹-黄陵野鶴行書 繁U)
    # note that this is a data issue in fact, <gbk> is not a OpenType supported encoding
    if encoding == 'x_mac_simp_chinese_ttx':
        try:
            return raw.decode('gbk'), IssueLevel.DATA, None
        except UnicodeDecodeError: pass

    # try just recover from truncated data (eg: 文鼎勘亭流)
    try:
        return decode(encoding)
    except UnicodeDecodeError: pass

    # the last hope (eg: 蘇新詩卵石體簡)
    return decode('utf_16_be')


preferred_langs = [
    2052, 33,  # zh-Hans
    1028, 19,  # zh-Hant
    1041, 11,  # jp
    1042, 23,  # kr
    1033, 0,   # en-US
]


def get_display_name(font, preferred_langs=preferred_langs):
    names = {n.langID: n for n in font['name'].names if n.nameID == 4}
    name = next(decode_name(names[lang])[0].strip('\x00') for lang in preferred_langs if lang in names)
    return name


def get_display_names(font_path, join=" & ", preferred_langs=preferred_langs):
    ext = os.path.splitext(font_path)[1].lower()
    if (ext == ".ttc" or ext == ".otc"):
        tt = ttLib.TTCollection(font_path)
        names = [get_display_name(font, preferred_langs) for font in tt.fonts]
    else:
        tt = ttLib.TTFont(font_path)
        names = [get_display_name(tt, preferred_langs)]
    tt.close()

    if (join is not None):
        return join.join(names)
    else:
        return(names)
