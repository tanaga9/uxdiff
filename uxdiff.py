#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from __future__ import print_function

"""
Compare two text files or directories (or sequences); generate the differences.
"""

__version__=  '1.5.0'


# The MIT License (MIT)
# --------------------------------------------
# Copyright (c) 2011,2016 Tanaga
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR
# A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys, difflib, argparse, unicodedata, re, codecs
# import pprint, pdb

if sys.hexversion < 0x02070000:
    raise SystemExit('*** Requires python >= 2.7.0')    # pragma: no cover

import filecmp
import os, stat
try: import io # python2.x
except(ImportError): pass # python3.x

import itertools
try:   itertools.filterfalse # python3.x
except(AttributeError):
    itertools.filterfalse = itertools.ifilterfalse # python2.x
    itertools.zip_longest = itertools.izip_longest

import functools

BUFSIZE = 8*1024

colormodes = {'always': True, 'never': False, 'auto': None}

global_withbg = False
def getcolor(withcolor, tag, side, openclose, isdircmp=False, withbg=None):
    if not withcolor: return ''
    if withbg is None: withbg = global_withbg
    bg1 = '' if not withbg else ';47'
    bg2 = '' if not withbg else ';47'
    bold = ';1'

    ansi_colors = {
        'red': '31',
        'grn': '32',
        'ylw': '33',
        'ble': '34',
        }
    colors = {
        '<': (('\033[' + ansi_colors['red'] + bg2 + bold + 'm', '\033[0m'),
              ('', '')),
        '>': (('', ''),
              ('\033[' + ansi_colors['grn'] + bg2 + bold + 'm', '\033[0m')),
        '|': ((('\033[' + ansi_colors['ble'] + bg2 + bold + 'm', '\033[0m'),
               ('\033[' + ansi_colors['ble']  + bg2 + bold + 'm', '\033[0m'))
               if isdircmp else (('', ''), ('', ''))),
        '-': (('\033[' + ansi_colors['red'] + bg1 + bold + 'm', '\033[0m'),
              ('', '')),
        '+': (('', ''),
              ('\033[' + ansi_colors['grn'] + bg1 + bold + 'm', '\033[0m')),
        '!': (('\033[' + ansi_colors['red'] + bg1 + bold + 'm', '\033[0m'),
              ('\033[' + ansi_colors['grn'] + bg1 + bold + 'm', '\033[0m')),
        '?': (('\033[' + ansi_colors['ylw'] + bg1 + bold + 'm', '\033[0m'),
              ('\033[' + ansi_colors['ylw'] + bg1 + bold + 'm', '\033[0m')),
        ' ': (('', ''), ('', '')),
        }
    return colors[tag][side][openclose]

def is_text(filepath):
    bufsize = BUFSIZE
    fp = open(filepath, 'rb')
    try:
        while True:
            buff = fp.read(bufsize)
            if len(buff) == 0: break
            try:
                if '\0' in buff: # python2.x
                    return False
            except TypeError:
                if 0    in buff: # python3.x
                    return False
    finally:
        fp.close()
    return True

# 文字列の幅(文字幅)を返す関数。
# 等幅フォントで表示されるASCII文字の横幅を1とする
# (この関数は幅広文字を表示する環境のためにある)
def strwidth(text, ambiguous_wide=True):
    """A function to give back the width (a character width) of string.

    Unit of width is one ASCII displayed by a monospaced font
    (This function is for environment using a wide character for)

    Example:

    >>> strwidth('teststring')
    10
    """

    # 文字幅の合計をリセット
    width = 0
    # 文字列を文字ごとに走査
    for char in text:
        # 幅広文字の判定
        if ord(char) < 256:
            # 確実にシングルバイト文字だと分かる場合は幅は1
            width += 1
        else:
            # Unicodeのデータベースに用意されている幅情報を使用する。
            # ただし曖昧(Ambiguous)の場合だけは文脈により文字幅が変わるので、
            # 幅1か幅2のどちらかを引数で指定できるようにする
            # 詳細はWikipediaの「東アジアの文字幅」などを参照
            #
            # F [幅2] (Fullwidth; 全角) - 互換分解特性 <wide> を持つ互換文字。
            #    文字の名前に "FULLWIDTH" を含む。いわゆる全角英数など。
            # H [幅1] (Halfwidth; 半角) - 互換分解特性 <narrow> を持つ互換文字。
            #    文字の名前に "HALFWIDTH" を含む。いわゆる半角カナなど。
            # W [幅2] (Wide; 広) - 上記以外の文字で、従来文字コードではいわゆる全角であったもの。
            #    漢字や仮名文字、東アジアの組版にしか使われない記述記号 (たとえば句読点) など。
            # Na [幅1] (Narrow; 狭) - 上記以外の文字で、従来文字コードでは対応する
            #    いわゆる全角の文字が存在したもの。いわゆる半角英数など。
            # A [幅1or幅2] (Ambiguous; 曖昧) - 文脈によって文字幅が異なる文字。
            #    東アジアの組版とそれ以外の組版の両方に出現し、東アジアの従来文字コードでは
            #    いわゆる全角として扱われることがある。ギリシア文字やキリル文字など。
            # N [幅1] (Neutral; 中立) - 上記のいずれにも属さない文字。
            #    東アジアの組版には通常出現せず、全角でも半角でもない。アラビア文字など。

            east_asian_width = unicodedata.east_asian_width(char)
            # 確実に幅広文字なので幅は2
            if east_asian_width in ['F', 'W']: width += 2
            # 文字の横幅が良く分からない場合は引数に任せる
            elif east_asian_width in ['A']:
                # 曖昧(Ambiguous)が幅2の場合
                if ambiguous_wide: width += 2
                # 曖昧(Ambiguous)が幅1の場合
                else: width += 1
            # Unicodeではあるが、幅は1
            else: width += 1
    # 文字列全体の文字幅を返す
    return width

if hasattr(functools, 'lru_cache'):
    strwidth = functools.lru_cache(maxsize=1024)(strwidth)

# タブ文字を展開する。（マルチバイト文字をサポート）
def expandtabs(text, tabsize=8, expandto='\t'):
    r"""Expand tabs(supports multibytes chars)

    Example:

    >>> expandtabs('text')
    'text'

    >>> expandtabs('\ta\tab\tend')
    '\t\t\t\t\t\t\t\ta\t\t\t\t\t\t\tab\t\t\t\t\t\tend'

    >>> expandtabs('abcdabc\tabcdabcd\tabcdabcda\tend')
    'abcdabc\tabcdabcd\t\t\t\t\t\t\t\tabcdabcda\t\t\t\t\t\t\tend'

    >>> expandtabs('\ta\tab\tabc\tabcd\tend', tabsize=4, expandto='@')
    '@@@@a@@@ab@@abc@abcd@@@@end'

    """
    index = text.find('\t')
    while index != -1:
        real_tabsize = tabsize - strwidth(text[:index]) % tabsize
        text = text[:index] + (expandto * real_tabsize) + text[index + 1:]
        index = text.find('\t', index + real_tabsize)

    return text

# 文字列を指定された幅で分割する
def strwidthdiv(text, width=180):
    """divide string by appointed width

    Example:

    >>> strwidthdiv('teststring', 2)
    ['te', 'st', 'st', 'ri', 'ng']

    >>> strwidthdiv('teststring', 3)
    ['tes', 'tst', 'rin', 'g']

    >>> strwidthdiv('teststring', 8)
    ['teststri', 'ng']

    >>> strwidthdiv('teststring', 15)
    ['teststring']
    """

    # 初期化
    array = []
    strbuffer = ''
    strbuffer_width = 0
    # 文字列を文字ごとに走査
    for char in text:
        # 文字幅を文字列長に加算する
        strbuffer_width += strwidth(char)
        # もし折り返し文字幅を超えている場合は文字列を折り返す
        if strbuffer_width > width:
            # バッファの文字列を配列に加える
            array.append(strbuffer)
            strbuffer = char
            strbuffer_width = strwidth(char)
        else:
            # 文字を連結する
            strbuffer += char
    # バッファの文字列を配列に加える
    array.append(strbuffer)

    return array


# 複数の文字列を指定された幅で同期を取って分割する
def strwidthdivsync(textarray, width=180):
    """synclonize divide some string by appointed width

    Example:

    >>> strwidthdivsync(('test', 'string', ''), width=2)
    [['te', 'st', ''], ['st', 'ri', 'ng'], ['', '', '']]

    >>> strwidthdivsync(('test', 'string', ''), width=3)
    [['tes', 't'], ['str', 'ing'], ['', '']]
    """

    # 初期化
    array = []
    strbuffer = []
    pos = []
    char = []
    strbuffer_width = 0

    # 文字列の数だけ初期化する
    for i, text in enumerate(textarray):
        array.append([])
        strbuffer.append('')
        pos.append(0)
        char.append('')

    while True:
        # 複数の文字列の中から1文字を抜き出し、
        # その中から最大の横幅(1 or 2)を計算する
        # 範囲外の例外を抑止して空文字を返すために前後両方を指定してスライスする
        maxwidth = max([strwidth(text[pos[i]:pos[i]+1])
                        for i, text in enumerate(textarray)])

        # 最大の横幅(1 or 2)分だけ切り出す
        for i, text in enumerate(textarray):
            # 範囲外の例外を抑止して空文字を返すために前後両方を指定してスライスする
            char[i] = strwidthdiv(text[pos[i]:], maxwidth)[0]
            # 先頭のポインタをずらす
            pos[i] += len(char[i])
        if ''.join(char) == '': break

        # 文字幅を文字列長に加算する
        strbuffer_width += maxwidth
        # もし折り返し文字幅を超えている場合は文字列を折り返す
        if strbuffer_width > width:
            # バッファの文字列を配列に加える
            for i, text in enumerate(textarray):
                array[i].append(strbuffer[i])
                strbuffer[i] = char[i]
            strbuffer_width = maxwidth
        else:
            # 文字を連結する
            for i, text in enumerate(textarray):
                strbuffer[i] += char[i]
    # バッファの文字列を配列に加える
    for i, text in enumerate(textarray):
        array[i].append(strbuffer[i])

    return array


# テキスト差分取得クラス
# 内部処理にdifflibのSequenceMatcherクラスを使用している
class Differ:
    r"""Differ is a class for comparing sequences.

    Differ uses SequenceMatcher both to compare sequences.
    """

    # Differクラスの初期化処理、
    # いくつかのオプションを指定できる。
    #   * cutoff
    #      SequenceMatcherクラスによって変更が検出されたチェンジセットに対して
    #      前後で異なる行であると判別する最低の割合。
    #      cutoff=0をfuzzy=1と共に指定するとsdiffコマンドと同様の出力が得られる
    #   * fuzzy
    #      SequenceMatcherクラスによって通常変更が検出されたチェンジセットの中で
    #      ベストにマッチした行、次にベストにマッチした行・・・と比較とマッチングを行うが
    #      その際にベストではないにしても登場順（行番号）が近いことを優先して
    #      マッチングを行う場合のベストマッチからの相対割合、
    #      cutoffに0を指定し、すべての変更チェンジセットを必ず最大限にマッチさせ
    #      fuzzyに1を指定し、マッチ率に依存しない登場順のみを考慮したマッチングを
    #      行えば、sdiffコマンドと同様の出力が得られる
    #   * cutoffchar
    #      cutoffオプションの行内差分ヴァージョン。
    #      行内差分での変更が検出された箇所で同期を取るかを指定する。
    #   * context
    #      差分をコンテキストで取得するか、その場合の前後行の数を指定する。
    #      差分をすべてフルで出力する場合はNoneを指定する。
    def __init__(self, linejunk=None, charjunk=None, cutoff=0.75, fuzzy=0.0,
                 cutoffchar=False, context=3):
        """Construct a text differencer, with options.

        """

        self.linejunk = linejunk
        self.charjunk = charjunk
        self.cutoff = cutoff
        self.fuzzy = fuzzy
        self.cutoffchar = cutoffchar
        self.context = context
        return

    # 2つのテキストの差分を取得する
    def compare(self, seq1, seq2):
        r"""
        Compare two sequences; return a generator of differences.

        Requirement is

        * both sequences must be iterable (no generator).
        * items in a sequence must be (recursively) hashable.

        If the items of a sequences are iterable, detect similar ones as needed.

        * Examples of hashable and iterable object (containing only hashable objects)
            * string
            * bytes
            * tuple
            * namedtuple
            * frozenset
            * frozendict
            * ...


        Example:

        >>> import pprint
        >>>
        >>> pprint.pprint(list(Differ().compare([
        ...    1, 2, 3, (4, 5), 6, 7, 8
        ... ], [
        ...    1, 2, 33, 4, 5, 6, 7, 8
        ... ])))
        [True,
         ((' ', 0, 1, 0, 1), None),
         ((' ', 1, 2, 1, 2), None),
         False,
         True,
         (('|', 2, 3, 2, 33), None),
         (('|', 3, (4, 5), 3, 4), None),
         (('>', None, None, 4, 5), None),
         False,
         True,
         ((' ', 4, 6, 5, 6), None),
         ((' ', 5, 7, 6, 7), None),
         ((' ', 6, 8, 7, 8), None),
         False]
        >>>
        >>> text1 = '''one
        ... two
        ... three
        ... '''.splitlines(1)
        >>>
        >>> text2 = '''ore
        ... tree
        ... emu
        ... '''.splitlines(1)
        >>>
        >>> pprint.pprint(list(Differ().compare(text1, text2)), width=100)
        [True,
         (('>', None, None, 0, 'ore\n'), None),
         (('<', 0, 'one\n', None, None), None),
         (('<', 1, 'two\n', None, None), None),
         (('|', 2, 'three\n', 1, 'tree\n'), [(' ', 't', 't'), ('-', 'h', None), (' ', 'ree\n', 'ree\n')]),
         (('>', None, None, 2, 'emu\n'), None),
         False]
        >>>
        >>> # like sdiff
        >>> pprint.pprint(list(Differ(cutoff=0, fuzzy=1).compare(text1, text2)), width=100)
        [True,
         (('|', 0, 'one\n', 0, 'ore\n'), [(' ', 'o', 'o'), ('!', 'n', 'r'), (' ', 'e\n', 'e\n')]),
         (('|', 1, 'two\n', 1, 'tree\n'), [(' ', 't', 't'), ('!', 'wo', 'ree'), (' ', '\n', '\n')]),
         (('|', 2, 'three\n', 2, 'emu\n'),
          [('-', 'thr', None), (' ', 'e', 'e'), ('!', 'e', 'mu'), (' ', '\n', '\n')]),
         False]
        >>>
        >>> text1 = '''  1. Beautiful is better than ugly.
        ...   2. Explicit is better than implicit.
        ...   3. Simple is better than complex.
        ...   4. Complex is better than complicated.
        ... '''.splitlines(1)
        >>>
        >>> text2 = '''  1. Beautiful is better than ugly.
        ...   3.   Simple is better than complex.
        ...   4. Complicated is better than complex.
        ...   5. Flat is better than nested.
        ... '''.splitlines(1)
        >>>
        >>> diff = Differ().compare(text1, text2)
        >>> pprint.pprint(list(diff), width=120)
        [True,
         ((' ', 0, '  1. Beautiful is better than ugly.\n', 0, '  1. Beautiful is better than ugly.\n'), None),
         False,
         True,
         (('<', 1, '  2. Explicit is better than implicit.\n', None, None), None),
         (('|', 2, '  3. Simple is better than complex.\n', 1, '  3.   Simple is better than complex.\n'),
          [(' ', '  3.', '  3.'),
           ('+', None, '  '),
           (' ', ' Simple is better than complex.\n', ' Simple is better than complex.\n')]),
         (('|', 3, '  4. Complex is better than complicated.\n', 2, '  4. Complicated is better than complex.\n'),
          [(' ', '  4. Compl', '  4. Compl'),
           ('+', None, 'icat'),
           (' ', 'e', 'e'),
           ('!', 'x', 'd'),
           (' ', ' is better than compl', ' is better than compl'),
           ('-', 'icat', None),
           (' ', 'e', 'e'),
           ('!', 'd', 'x'),
           (' ', '.\n', '.\n')]),
         (('>', None, None, 3, '  5. Flat is better than nested.\n'), None),
         False]
         
        +------------+--------------------------------------------------------------------------------------------+
        | Yields     | Meaning                                                                                    |
        +============+============================================================================================+
        | True       | begin of a group of diff                                                                   |
        +------------+--------------------------------------------------------------------------------------------+
        | False      | end of a group of diff                                                                     |
        +------------+--------------------------------------------------------------------------------------------+
        | None       | omitted matches beyond the number of contexts                                              |
        +------------+--------------------------------------------------------------------------------------------+
        | Tuple      | ((Code, Index1 | None, Item1 | None, Index2 | None, Item2 | None), InlineDiff | None)      |
        +------------+--------------------------------------------------------------------------------------------+

        +------------+------------------------------------+
        | Code       | Meaning                            |
        +============+====================================+
        | "<"        | unique to sequence 1               |
        +------------+------------------------------------+
        | ">"        | unique to sequence 2               |
        +------------+------------------------------------+
        | " "        | common to both sequences           |
        +------------+------------------------------------+
        | "|"        | different to both sequences        |
        +------------+------------------------------------+

        +------------+--------------------------------------------------------------------+
        | InlineDiff | Meaning                                                            |
        +============+====================================================================+
        | None       | There is no InlineDiff (Code is not "|" or items are not iterable) |
        +------------+--------------------------------------------------------------------+
        | List       | [(InlineCode, SlicedItem1 | None, SlicedItem2 | None), ... ]       |
        +------------+--------------------------------------------------------------------+

        +------------+------------------------------------------------------+
        | InlineCode | Meaning                                              |
        +============+======================================================+
        | "-"        | unique to inline sequence 1 (item of sequence 1)     |
        +------------+------------------------------------------------------+
        | "+"        | unique to inline sequence 2 (item of sequence 2)     |
        +------------+------------------------------------------------------+
        | " "        | common to both inline sequences                      |
        +------------+------------------------------------------------------+
        | "!"        | different to both inline sequences                   |
        +------------+------------------------------------------------------+

        """

        # SequenceMatcherのインスタンスを生成する
        cruncher = difflib.SequenceMatcher(self.linejunk, seq1, seq2)

        # コンテキスト差分オプションがNoneでない場合は
        if self.context != None:
            # get_grouped_opcodesを使う
            opcodes = cruncher.get_grouped_opcodes(self.context)
        else:
            # get_opcodesを使う、ただしget_grouped_opcodesとインタフェースを
            # 合わせるために呼び出した後1枚リストをかぶせる
            opcodes = [cruncher.get_opcodes()]

        max_seq1_high = 0
        max_seq2_high = 0
        # 差分の纏まりのグループごとにループする
        for i, opcode in enumerate(opcodes):
            # 差分の纏まりごとにループする
            for h, (tag,
                 seq1_low, seq1_high,
                 seq2_low, seq2_high) in enumerate(opcode):
                max_seq1_high = max(max_seq1_high, seq1_high)
                max_seq2_high = max(max_seq2_high, seq2_high)
                if i == 0 and h == 0 and (seq1_low > 0 or seq2_low > 0):
                    yield None
                yield True
                # タグが変更の場合は
                if   tag == 'replace':
                    try:
                        for num1, num2 in itertools.zip_longest(
                            range(seq1_low, seq1_high),
                            range(seq2_low, seq2_high)):
                            if num1 is not None: iter(seq1[num1])
                            if num2 is not None: iter(seq2[num2])
                    except TypeError:
                        for num1, num2 in itertools.zip_longest(
                            range(seq1_low, seq1_high),
                            range(seq2_low, seq2_high)):
                            code = '|'
                            if   num1 is None:
                                code = '>'
                            elif num2 is None:
                                code = '<'
                            yield ((code,
                                    num1, seq1[num1] if num1 is not None else None,
                                    num2, seq2[num2] if num2 is not None else None), None)
                    else:
                        # さらにその変更の纏まり（複数item）のなかから、
                        # もっともマッチしたitemを検知し、その前後で
                        # 再びもっともマッチしたitemを検知し、その前後で・・・
                        # という再帰処理を行い、もっとも見た目が良い前後比較を作成する
                        gen = self._fancy_replace(seq1, seq1_low, seq1_high,
                                                  seq2, seq2_low, seq2_high)
                        # ジェネレータを受け取るので要素を生成してyieldする
                        for line in gen:
                            yield line
                # タグが削除の場合は
                elif tag == 'delete':
                    # 削除分のitemを個別に生成して返す
                    # 削除のタグは'<'とし、必要のない情報についてはNoneで返す
                    for num1 in range(seq1_low, seq1_high):
                        yield (('<', num1, seq1[num1], None, None), None)
                # タグが追加の場合は
                elif tag == 'insert':
                    # 追加分のitemを個別に生成して返す
                    # 追加のタグは'>'とし、必要のない情報についてはNoneで返す
                    for num2 in range(seq2_low, seq2_high):
                        yield (('>', None, None, num2, seq2[num2]), None)
                # タグが一致の場合は
                elif tag == 'equal':
                    # 互いのitem数が一致することをassertで確認する
                    assert seq1_high - seq1_low == seq2_high - seq2_low
                    # 一致分のitemを個別に生成して返す
                    # 一致のタグは' 'とし、必要のない情報についてはNoneで返す
                    for num1, num2 in zip(range(seq1_low, seq1_high),
                                          range(seq2_low, seq2_high)):
                        yield ((' ', num1, seq1[num1], num2, seq2[num2]), None)
                # その他のタグを受け取った場合は
                else:
                    # 予定外なので例外を飛ばす
                    raise ValueError('unknown tag \'' + tag + '\'')

                yield False
            # コンテキストの終わりをあらわすNoneを返す
            if self.context != None and (max_seq1_high < len(seq1) or max_seq2_high < len(seq2)):
                yield None
        return

    # 1ブロックの線をもう一つと入れ替えるとき、
    # *similar*線を求めてブロックを捜してください;
    # 最もあっている一組（あるとしても）が同期点として使われます、
    # そして、ライン内違い採点は類似した一組の上でされます。
    # しばしばそれの価値があるが、たくさんの仕事。
    def _fancy_replace(self,
                       seq1, seq1_low, seq1_high,
                       seq2, seq2_low, seq2_high):
        r"""
        When replacing one block of lines with another, search the blocks
        for *similar* lines; the best-matching pair (if any) is used as a
        synch point, and intraline difference marking is done on the
        similar pair. Lots of work, but often worth it.

        Example:

        >>> text1 = '''teststring
        ... '''.splitlines(1)
        >>>
        >>> text2 = '''poststream
        ... '''.splitlines(1)
        >>>
        >>> import pprint
        >>>
        >>>
        >>> #pprint.pprint(list(Differ().compare(text1, text2)), width=100)
        >>>
        >>> results = Differ()._fancy_replace(text1, 0, 1,
        ...                                   text2, 0, 1)
        >>> pprint.pprint(list(results))
        [(('<', 0, 'teststring\n', None, None), None),
         (('>', None, None, 0, 'poststream\n'), None)]
        >>>
        >>> results = Differ(cutoff=0, fuzzy=1)._fancy_replace(text1, 0, 1,
        ...                                                    text2, 0, 1)
        >>> pprint.pprint(list(results))
        [(('|', 0, 'teststring\n', 0, 'poststream\n'),
          [('!', 'te', 'po'),
           (' ', 'ststr', 'ststr'),
           ('!', 'ing', 'eam'),
           (' ', '\n', '\n')])]
        >>>
        >>> results = Differ(cutoff=0, fuzzy=1, cutoffchar=True)._fancy_replace(text1, 0, 1,
        ...                                                                     text2, 0, 1)
        >>> pprint.pprint(list(results))
        [(('|', 0, 'teststring\n', 0, 'poststream\n'),
          [('-', 'te', None),
           ('+', None, 'po'),
           (' ', 'ststr', 'ststr'),
           ('-', 'ing', None),
           ('+', None, 'eam'),
           (' ', '\n', '\n')])]
        """

        # don't synch up unless the lines have a similarity score of at
        # least cutoff; best_ratio tracks the best score seen so far
        # 文字列がcutoffに到達しない場合は左右に並べません
        # best_ratioは、それまでで最もマッチした割合を記憶しています
        best_ratio = self.cutoff
        best_found = False
        cruncher = difflib.SequenceMatcher(self.charjunk)
        # 1st indices of equal lines (if any)
        equal_seq1_pos, equal_seq2_pos = None, None

        # search for the pair that matches best without being identical
        # (identical lines must be junk lines, & we don't want to synch up
        # on junk -- unless we have to)
        # まったく同一ではなく、かつ最もマッチする一組をサーチする
        # （同一の文字列はジャンク文字列でなければならない、
        # 　特別そうしたい場合以外は、ジャンクで同期すべきではない）

        # seq2について繰り返し処理する
        for seq2_pos in range(seq2_low, seq2_high):
            # 取得したseq2の1itemをSequenceMatcherにセットする
            cruncher.set_seq2(seq2[seq2_pos])
            # seq1について繰り返し処理する
            for seq1_pos in range(seq1_low, seq1_high):
                # 取得したseq1の1itemとseq2の1itemが完全一致する場合は
                if seq1[seq1_pos] == seq2[seq2_pos]:
                    # すでに完全一致ペアが見つかって居ない場合は
                    if equal_seq1_pos is None:
                        # 今回のペアを最初の完全一致ペアとして記憶する
                        equal_seq1_pos = seq1_pos
                        equal_seq2_pos = seq2_pos
                    # このペアでやるべきことは何も無いので次のループへ
                    continue

                # 取得したseq1の1itemをSequenceMatcherにセットする
                cruncher.set_seq1(seq1[seq1_pos])
                # computing similarity is expensive, so use the quick
                # upper bounds first -- have seen this speed up messy
                # compares by a factor of 3.
                # note that ratio() is only expensive to compute the first
                # time it's called on a sequence pair; the expensive part
                # of the computation is cached by cruncher
                # 類似性の計算にはコストが掛かるので、
                # まずは上限の境界をすばやく判定する。
                # （これで比較の速度が3倍に上がることがある）
                # ratio()よりも限定された機能をもったquick_ratio()
                # もしくはreal_quick_ratio()を最初に試す。
                # 計算の高価な一部は、クランチャーによって貯蔵されます

                # すでにベストマッチが見つかっていれば
                # fuzzyを設定する
                if best_found: fuzzy = self.fuzzy
                # それ以外の場合はfuzzyに0をセットする
                else: fuzzy = 0

                # この文字列全体のマッチ率を返す3つのメソッドは、
                # 異なる近似値に基づく異なる結果を返す。
                # とはいえ、quick_ratio()と real_quick_ratio()は、
                # 常にratio()より大きな値を返す。
                # >>> s = SequenceMatcher(None, "abcd", "bcde")
                # >>> s.ratio()
                # 0.75
                # >>> s.quick_ratio()
                # 0.75
                # >>> s.real_quick_ratio()
                # 1.0
                if (cruncher.real_quick_ratio() > best_ratio + fuzzy
                and cruncher.quick_ratio()      > best_ratio + fuzzy
                and cruncher.ratio()            > best_ratio + fuzzy):
                    # 新たなベストマッチ（既存のベストマッチを
                    # 超えるマッチ率のペア）を見つけた
                    best_found = True
                    best_ratio = cruncher.ratio()
                    best_i = seq1_pos
                    best_j = seq2_pos

        # ------------------------------------------------------------

        # ベストマッチのマッチ率がcutoffを超えていない場合は
        if not best_ratio > self.cutoff:
            # no non-identical "pretty close" pair
            # 『同一でない「かなり近い」ペア』が無い

            # 同一のペアも無い場合は
            if equal_seq1_pos is None:
                # no identical pair either -- treat it as a straight replace
                # 単純に完全に置き換えられた文字列の集まりとする
                # '|'が存在せず、'>'および'<'、もしくは'>'および'<'
                # の集まりとする。
                # どちらが採用されるかはそれぞれのitem数によって決まる
                # itemが少ないほうが先に返される。

                # dump the shorter block first -- reduces the burden on short-term
                # memory if the blocks are of very different sizes
                # 最初により少ないitem数を処理する
                # これはitem数非常に異なるサイズの場合に、メモリ上の負荷を減らす効果がある

                # seq2のほうがseq1よりitem数が少ない場合は
                if seq2_high - seq2_low < seq1_high - seq1_low:
                    # seq2について全itemを'>'としてyieldする
                    for num2 in range(seq2_low, seq2_high):
                        yield (('>', None, None, num2, seq2[num2]), None)
                    # seq1について全itemを'<'としてyieldする
                    for num1 in range(seq1_low, seq1_high):
                        yield (('<', num1, seq1[num1], None, None), None)
                # seq1のほうがseq2よりitem数が少ない場合は
                else:
                    # seq1について全itemを'<'としてyieldする
                    for num1 in range(seq1_low, seq1_high):
                        yield (('<', num1, seq1[num1], None, None), None)
                    # seq2について全itemを'>'としてyieldする
                    for num2 in range(seq2_low, seq2_high):
                        yield (('>', None, None, num2, seq2[num2]), None)
                return
            # no close pair, but an identical pair -- synch up on that
            # 『同一でない「かなり近い」ペア』は無いが、
            # 同一のペアがあるので、それで同期を取る
            best_i = equal_seq1_pos
            best_j = equal_seq2_pos
            best_ratio = 1.0
        else:
            # there's a close pair, so forget the identical pair (if any)
            # 『同一でない「かなり近い」ペア』が有る。
            # そのため、同一のペアを忘れる（たとえあるとしても）
            equal_seq1_pos = None

        # ------------------------------------------------------------

        # a[best_i] very similar to b[best_j]; equal_seq1_pos is None iff they're not
        # identical
        # この時点ではseq1[best_i]とseq2[best_j]は最適なペア（同一であるか
        # もしくは非常に似ているペア）となっている
        # 同一のペアである場合は、equal_seq1_posはNoneではない
        # 非常に似ているペアの場合は、equal_seq1_posはNoneとなっている

        # pump out diffs from before the synch point
        # 同期点（最適なペア）で区切った場合の前半に対して
        # 再帰的に同じ処理を行う（前半がなくなるまで続く）
        for line in self._fancy_helper(seq1, seq1_low, best_i,
                                       seq2, seq2_low, best_j):
            yield line

        # do intraline marking on the synch pair
        # 最適なペアについてitem内差分を取得する
        seq1_elt = seq1[best_i]
        seq2_elt = seq2[best_j]

        # 非常に似ているペアの場合は（同一のペアでない場合は）
        if equal_seq1_pos is None:
            # pump out a '-', '?', '+', '?' quad for the synched lines
            # 同期する文字列に対して判定を行い、'!' '-' '+' ' ' を設定する
            #   * '!' : 変更
            #   * '-' : 削除
            #   * '+' : 追加
            #   * ' ' : 同一
            line_tags = ''
            # SequenceMatcherを使用して差分を取得する
            cruncher.set_seqs(seq1_elt, seq2_elt)

            linediff_list = []
            # 差分をグループごとに取得
            for (tag,
                 seq1_i1, seq1_i2,
                 seq2_j1, seq2_j2) in cruncher.get_opcodes():

                # グループ内のそれぞれの文字数を記憶する
                la = seq1_i2 - seq1_i1
                lb = seq2_j2 - seq2_j1

                seq1_elta = seq1_elt[seq1_i1:seq1_i2]
                seq2_elta = seq2_elt[seq2_j1:seq2_j2]

                # 変更の場合
                if   tag == 'replace':
                    # 変更した文字をすべて同期して'!'で返すか、
                    # 個別に'-'および'+'で返すかを判定する
                    # （ratio()は0であることが確定しているので計算しない）
                    # （メモリの負荷はそれほど考慮しなくてよいので'+'および'-'では
                    # 　表示しない）
                    if self.cutoffchar:
                        # 個別に'-'および'+'で表示する
                        linediff_list.append(('-', seq1_elta, None))
                        linediff_list.append(('+', None, seq2_elta))
                    else:
                        # すべて同期して'!'で表示する
                        linediff_list.append(('!', seq1_elta, seq2_elta))
                # 削除の場合
                elif tag == 'delete': linediff_list.append(('-', seq1_elta, None))
                # 追加の場合
                elif tag == 'insert': linediff_list.append(('+', None, seq2_elta))
                # 同一の場合
                elif tag == 'equal': linediff_list.append((' ', seq1_elta, seq2_elta))
                # その他のタグを受け取った場合は
                else:
                    # 予定外なので例外を飛ばす
                    raise ValueError('unknown tag \'' + tag + '\'')
            yield (('|', best_i, seq1_elt, best_j, seq2_elt), linediff_list)
        else:
            # the synch pair is identical
            # ペアは同一
            yield ((' ', best_i, seq1_elt, best_j, seq2_elt), None)

        # pump out diffs from after the synch point
        # 同期点（最適なペア）で区切った場合の後半に対して
        # 再帰的に同じ処理を行う（後半がなくなるまで続く）
        for line in self._fancy_helper(seq1, best_i+1, seq1_high,
                                       seq2, best_j+1, seq2_high):
            yield line

        return

    # _fancy_replace()内から分割点の前半と後半の2回再帰的に
    # 呼び出される際に使用される関数
    def _fancy_helper(self,
                      seq1, seq1_low, seq1_high,
                      seq2, seq2_low, seq2_high):
        g = []
        # seq1が存在する
        if seq1_low < seq1_high:
            # seq2が存在する
            if seq2_low < seq2_high:
                # seq1とseq2が両方存在するので
                # _fancy_replace()を再帰的に呼び出す
                g = self._fancy_replace(seq1, seq1_low, seq1_high,
                                        seq2, seq2_low, seq2_high)
                # イテレータが返るのでそのままyieldする
                for line in g:
                    yield line
            else:
                # seq1が存在してseq2が無いので、
                # seq1について'<'で返す
                for num1 in range(seq1_low, seq1_high):
                    yield (('<', num1, seq1[num1], None, None), None)
        # seq2が存在する
        elif seq2_low < seq2_high:
            # seq2が存在してseq1が無いので、
            # seq2について'>'で返す
            for num2 in range(seq2_low, seq2_high):
                yield (('>', None, None, num2, seq2[num2]), None)
        return

    @staticmethod
    def _colordiff(text_array, linediff, side): # side is 0(left) or 1(right)
        colortext_array = []
        index = 0
        index_linediff = 0
        for text in text_array:
            colortext = ''
            while len(text) > 0:
                if linediff[index][side + 1] is None:
                    index += 1
                    index_linediff = 0
                    continue
                chartag = linediff[index][0]
                linediff_delta = linediff[index][side + 1][index_linediff:]
                minlen = min((len(text), len(linediff_delta)))
                text = text[minlen:]
                deltatext = linediff_delta[:minlen].replace('\t', ' ')

                scolor  = getcolor(True, chartag, side, 0)
                ecolor  = getcolor(True, chartag, side, 1)

                colortext += scolor
                colortext += deltatext
                colortext += ecolor

                if len(linediff_delta) == minlen:
                    index += 1
                    index_linediff = 0
                else:
                    index_linediff += minlen
            colortext_array.append(colortext)
        return colortext_array

    def pretty_compare(self, lines1, lines2, width, withcolor=False, offset1=0, offset2=0):
        for diff in self.compare(lines1, lines2):
            if   diff is None:
                for textlinediff in self.textlinediffs():
                    yield textlinediff
            elif diff is True:
                for textdiff in self.begin_textdiffs():
                    yield textdiff
            elif diff is False:
                for textdiff in self.end_textdiffs():
                    yield textdiff
            else:
                ((tag, num1, text1, num2, text2), linediff) = diff
                if num1 is not None: num1 += offset1
                if num2 is not None: num2 += offset2
                self.formattext(tag, num1, text1, num2, text2, width,
                    withcolor=withcolor, linediff=linediff)
                if tag == '|':
                    self.formatlinetext(num1, num2, linediff, width,
                        withcolor=withcolor)

                for textdiff in self.textdiffs():
                    yield textdiff
        else:
            for textlinediff in self.textlinediffs():
                yield textlinediff

    def formattext(self, tag, num1, text1, num2, text2, width, withcolor=False, linediff=None):
        raise NotImplementedError()
    def formatlinetext(self, num1, num2, linediff, width, withcolor=False):
        raise NotImplementedError()
    def textlinediffs(self):
        raise NotImplementedError()
    def begin_textdiffs(self):
        raise NotImplementedError()
    def end_textdiffs(self):
        raise NotImplementedError()
    def textdiffs(self):
        raise NotImplementedError()

class SidebysideDiffer(Differ):
    def __init__(self, *args, **kwargs):
        Differ.__init__(self, *args, **kwargs)
        self.array_textdiffs = []
        self.array_textlinediffs = []
        return

    # 差分についてプレーンテキストでフォーマッティングを行う関数
    # （行内差分についてはサポートしていない）
    def formattext(self, tag, num1, text1, num2, text2, width, withcolor=False, linediff=None):
        """

        Example:

        >>> differ = SidebysideDiffer()
        >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 80)
        >>> list(differ.textdiffs())
        ['     2|aaa                             |      3|bbb']

        >>> differ.formattext('|', 1, 'aaa', 2, 'bbb', 60)
        >>> list(differ.textdiffs())
        ['     2|aaa                   |      3|bbb']

        >>> differ.formattext(' ', 1, 'aaa', 2, 'aaa', 80)
        >>> list(differ.textdiffs())
        ['     2|aaa                                    3|aaa']

        >>> differ.formattext('<', 1, 'aaa', None, None, 80)
        >>> list(differ.textdiffs())
        ['     2|aaa                             <       |']

        >>> differ.formattext('>', None, None, 2, 'bbb', 80)
        >>> list(differ.textdiffs())
        ['      |                                >      3|bbb']

        >>> import pprint
        >>> differ.formattext(
        ...     '>',
        ...     1, 'a' * 60,
        ...     2, 'b' * 20, 60)
        >>> pprint.pprint(list(differ.textdiffs()))
        ['     2|aaaaaaaaaaaaaaaaaaaaa >      3|bbbbbbbbbbbbbbbbbbbb',
         '     ^|aaaaaaaaaaaaaaaaaaaaa ^       |',
         '     ^|aaaaaaaaaaaaaaaaaa    ^       |']
        """
        assert width >= (6 + 1 + 2) + (1 + 1 + 1) + (6 + 1 + 2)
        textwidth = int((width - ((6 + 1 + 0) + (1 + 1 + 1) + (6 + 1 + 0))) / 2)

        lines = []
        line = ''

        if num1  is None: num1  = ''
        if num2  is None: num2  = ''
        if text1 is None: text1 = ''
        if text2 is None: text2 = ''

        text1 = text1.rstrip('\r\n')
        text2 = text2.rstrip('\r\n')

        text1 = text1.replace('\t', ' ')
        text2 = text2.replace('\t', ' ')

        text1_array = strwidthdiv(text1, textwidth)
        text2_array = strwidthdiv(text2, textwidth)

        if tag == '|' and withcolor and linediff is not None:
            colortext1_array = Differ._colordiff(text1_array, linediff, 0)
            colortext2_array = Differ._colordiff(text2_array, linediff, 1)

        elif (tag == '<' or tag == '>') and withcolor:
            scolor  = getcolor(True, tag, 0, 0)
            ecolor  = getcolor(True, tag, 0, 1)
            colortext1_array = []
            for i, text1 in enumerate(text1_array):
                colortext1_array.append(scolor + text1 + ecolor)

            scolor  = getcolor(True, tag, 1, 0)
            ecolor  = getcolor(True, tag, 1, 1)
            colortext2_array = []
            for i, text2 in enumerate(text2_array):
                colortext2_array.append(scolor + text2 + ecolor)

        else:
            colortext1_array = text1_array
            colortext2_array = text2_array

        for i in range(max(len(text1_array), len(text2_array))):
            if isinstance(num1, int):
                if i == 0: pnum1 = str(num1 + 1)
                else: pnum1 = '^'
            else: pnum1 = ''
            if isinstance(num2, int):
                if i == 0: pnum2 = str(num2 + 1)
                else: pnum2 = '^'
            else: pnum2 = ''

            try: ptext1 = text1_array[i]
            except(IndexError):
                pnum1  = ''
                ptext1 = ''
            try: ptext2 = text2_array[i]
            except(IndexError):
                pnum2  = ''
                ptext2 = ''
            try: ctext1 = colortext1_array[i]
            except(IndexError):
                ctext1 = ''
            try: ctext2 = colortext2_array[i]
            except(IndexError):
                ctext2 = ''

            # (6 + 1 + x) + (1 + 1 + 1) + (6 + 1 + y)
            line += (pnum1.rjust(6))
            line += ('|')
            line += (ctext1)
            line += (max(textwidth - strwidth(ptext1), 0) * ' ' + '')
            if   i == 0:     line += (' ' + tag + ' ')
            elif tag == ' ': line += (' ' + ' ' + ' ')
            else:            line += (' ' + '^' + ' ')
            line += (pnum2.rjust(6))
            line += ('|')
            line += (ctext2)
            lines.append(line)
            line = ''
        self.array_textdiffs.append(lines)
        return

    # 行内差分についてプレーンテキストでフォーマッティングを行う関数
    def formatlinetext(self, num1, num2, linediff, width, withcolor=False):
        """

        Example:

        >>> import pprint
        >>> differ = SidebysideDiffer()
        >>> differ.formatlinetext(
        ...     1, 2,
        ...     [('!', 'bbb', 'aaaaa'),
        ...      (' ', 'cc', 'cc'),
        ...      ('+', None, 'dd'),
        ...      ('-', 'ee', None)], 80)
        >>> pprint.pprint(list(differ.textlinediffs()))
        ['',
         '[     ]      |!!!++  ++--',
         '[ <-  ]     2|bbb  cc  ee',
         '[  -> ]     3|aaaaaccdd  ',
         '']
        """
        if withcolor: return

        assert width >= (6 + 1 + 6 + 1 + 3)
        textwidth = width - (6 + 1 + 6 + 1 + 3)

        lines = []

        buffertag = ''
        buffertext1 = ''
        buffertext2 = ''
        for tag, text1, text2 in linediff:

            if text1 != None:
                text1 = text1.replace('\r', ' ')
                text1 = text1.replace('\n', ' ')
                text1 = text1.replace('\t', ' ')
            if text2 != None:
                text2 = text2.replace('\r', ' ')
                text2 = text2.replace('\n', ' ')
                text2 = text2.replace('\t', ' ')

            if   tag == ' ':
                buffertag   += ' ' * strwidth(text1)
                buffertext1 += text1
                buffertext2 += text2
            elif tag == '+':
                buffertag   += '+' * strwidth(text2)
                buffertext1 += ' ' * strwidth(text2)
                buffertext2 += text2
            elif tag == '-':
                buffertag   += '-' * strwidth(text1)
                buffertext1 += text1
                buffertext2 += ' ' * strwidth(text1)
            elif tag == '!':
                maxwidth = max(strwidth(text1), strwidth(text2))
                minwidth = min(strwidth(text1), strwidth(text2))
                subtag = '!'
                if strwidth(text1) < strwidth(text2):
                    subtag = '+'
                    buffertag += tag * minwidth + subtag * (strwidth(text2) - strwidth(text1))
                else:
                    subtag = '-'
                    buffertag += tag * minwidth + subtag * (strwidth(text1) - strwidth(text2))
                buffertext1 += text1[:minwidth]
                buffertext1 += text1[minwidth:]
                buffertext1 += ' ' * (maxwidth - strwidth(text1))
                buffertext2 += text2[:minwidth]
                buffertext2 += text2[minwidth:]
                buffertext2 += ' ' * (maxwidth - strwidth(text2))

        (taglines,
         text1lines,
         text2lines) = strwidthdivsync((buffertag,
                                        buffertext1,
                                        buffertext2),
                                        textwidth)

        for i in range(max(len(taglines), len(text1lines), len(text2lines))):
            line  = '[     ]'
            line += ' ' * 6
            line += '|'
            line += taglines[i]#.rstrip()
            lines.append(line)

            line  = '[ <-  ]'
            if i == 0: line += str(num1 + 1).rjust(6)
            else:      line += '^'.rjust(6)
            line += '|'
            line += text1lines[i]#.rstrip()
            lines.append(line)

            line  = '[  -> ]'
            if i == 0: line += str(num2 + 1).rjust(6)
            else:      line += '^'.rjust(6)
            line += '|'
            line += text2lines[i]#.rstrip()
            lines.append(line)

        self.array_textlinediffs.append(lines)
        return

    def textdiffs(self):
        for textdiff in self.array_textdiffs:
            for line in textdiff:
                yield line
        self.array_textdiffs = []

    def begin_textdiffs(self):
        if False: yield

    def end_textdiffs(self):
        if False: yield

    def textlinediffs(self):
        yield ''
        for textlinediff in self.array_textlinediffs:
            for line in textlinediff:
                yield line
            yield ''
        self.array_textlinediffs = []

class UniLikeDiffer(SidebysideDiffer):
    def __init__(self, *args, **kwargs):
        SidebysideDiffer.__init__(self, *args, **kwargs)
        self.array_textdiffs_delay = []
        return

    def formattext(self, tag, num1, text1, num2, text2, width, withcolor=False, linediff=None):

        assert width >= (6 + 1 + 6 + 1 + 3)
        textwidth = width - (6 + 1 + 6 + 1 + 3)

        lines = []

        if text1 is not None:
            text1 = text1.rstrip('\r\n')
            text1 = text1.replace('\t', ' ')
            text1_array = strwidthdiv(text1, textwidth)
        else:
            text1_array = []
        if text2 is not None:
            text2 = text2.rstrip('\r\n')
            text2 = text2.replace('\t', ' ')
            text2_array = strwidthdiv(text2, textwidth)
        else:
            text2_array = []

        if tag == '|' and withcolor and linediff is not None:
            colortext1_array = Differ._colordiff(text1_array, linediff, 0)
            colortext2_array = Differ._colordiff(text2_array, linediff, 1)

        elif tag == '<' and withcolor:
            scolor  = getcolor(True, tag, 0, 0)
            ecolor  = getcolor(True, tag, 0, 1)
            colortext1_array = []
            colortext2_array = []
            for i, text1 in enumerate(text1_array):
                colortext1_array.append(scolor + text1 + ecolor)

        elif tag == '>' and withcolor:
            scolor  = getcolor(True, tag, 1, 0)
            ecolor  = getcolor(True, tag, 1, 1)
            colortext1_array = []
            colortext2_array = []
            for i, text2 in enumerate(text2_array):
                colortext2_array.append(scolor + text2 + ecolor)

        else:
            colortext1_array = text1_array
            colortext2_array = text2_array

        for h, colortext_array in enumerate((colortext1_array, colortext2_array)):
            for i, colortext in enumerate(colortext_array):
                if i == 0:
                    if num1 is None: pnum1 = ''
                    else: pnum1 = str(num1 + 1)
                    if num2 is None: pnum2 = ''
                    else: pnum2 = str(num2 + 1)
                else:
                    if num1 is None: pnum1 = ''
                    else: pnum1 = '^'
                    if num2 is None: pnum2 = ''
                    else: pnum2 = '^'

                ptag = tag
                if tag == '|' and h == 0: ptag = '-'
                if tag == '|' and h == 1: ptag = '+'
                if tag == '<': ptag = '-'
                if tag == '>': ptag = '+'

                #if tag == ' ':
                if (h == 0 and (ptag == ' ' or ptag == '-')) or (h == 1 and ptag == '+'):
                    if withcolor:
                        scolor = ''
                        ecolor = ''
                        if ptag == '-':
                            scolor  = getcolor(True, ptag, 0, 0)
                            ecolor  = getcolor(True, ptag, 0, 1)
                        elif ptag == '+':
                            scolor  = getcolor(True, ptag, 1, 0)
                            ecolor  = getcolor(True, ptag, 1, 1)
                        cptag = scolor + ptag + ecolor
                        cpnum1 = scolor + pnum1.rjust(6) + ecolor
                        cpnum2 = scolor + pnum2.rjust(6) + ecolor
                    else:
                        cptag = ptag
                        cpnum1 = pnum1.rjust(6)
                        cpnum2 = pnum2.rjust(6)

                    line = ''
                    line += (' '*6 if ptag == '+' else cpnum1)
                    line += (' ')
                    line += (' '*6 if ptag == '-' else cpnum2)
                    line += ('|')
                    if   i == 0:     line += (' ' + cptag + ' ')
                    elif tag == ' ': line += (' ' + ' ' + ' ')
                    else:            line += (' ' + '^' + ' ')
                    line += colortext
                    lines.append(line)
            if h == 0:
                self.array_textdiffs.append(lines)
            else:
                self.array_textdiffs_delay.append(lines)
            lines = []
        return

    def end_textdiffs(self):
        for textdiff in self.array_textdiffs_delay:
            for line in textdiff:
                yield line
        self.array_textdiffs_delay = []

def tabulate(diffs, truncate=None):
    r"""
    Output the detected difference as an HTML table (for Jupyter).

    """

    class JupyterHTMLStr(str):
        def _repr_html_(self): return self
        @property
        def str(self): return self
    escape = (lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    nonetoe = (lambda s: s if s is not None else '')
    trunc = (lambda s, maxlen: s[:maxlen]+'...' if len(s) > maxlen else s)
    syltpl = 'text-align: start; background: {};'
    sylsep = ' style=" background: #f5f7f8;"'
    html = '''<table style="background: #f5f7f8; color: #000; width=100%; overflow-wrap: anywhere; text-align: start">
    <thead><tr><th>idx1</th><th>seq1</th><th></th><th>seq2</th><th>idx2</th><th></th>
    <th></th><th>slice1</th><th></th><th>slice2</th><th></th></tr></thead><tbody>'''
    for i, diff in enumerate(diffs):
        if diff is True:
            html += '<tr><td colspan="11"></td></tr>'
            continue
        if diff is False:
            html += '<tr><td colspan="11"></td></tr>'
            continue
        if diff is None:
            html += '<tr><td colspan="11" style="text-align: center; background: #E0F4FE;">...</td></tr>'
            continue
        ((code, idx1, seq1, idx2, seq2), idiffs) = diff
        bgc = bgc1 = bgcn1 = bgc2 = bgcn2 = '#fff'
        syladd = syladd1 = syladd2 = ""
        if code == '<':
            idx2, seq2 = nonetoe(idx2), nonetoe(seq2)
            bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#ffd7d5', '#ffebe9', '#ffd7d5', '#f5f7f8', '#f5f7f8')
            syladd += 'font-weight: bold; color: #700;'
            syladd1 += 'font-weight: bold; color: #700;'
        if code == '>':
            idx1, seq1 = nonetoe(idx1), nonetoe(seq1)
            bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#ccffd8', '#f5f7f8', '#f5f7f8', '#e6ffec', '#ccffd8')
            syladd += 'font-weight: bold; color: #040;'
            syladd2 += 'font-weight: bold; color: #040;'
        if code == '|':
            if idiffs is None:
                bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#f2e8ab', '#ffebe9', '#ffd7d5', '#e6ffec', '#ccffd8')
                syladd1 += 'font-weight: bold; color: #700;'
                syladd2 += 'font-weight: bold; color: #040;'
            else:
                bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#f2e8ab', '#ffebe9', '#ffebe9', '#e6ffec', '#e6ffec')
            syladd += 'font-weight: bold; color: #330;'
        syl = ' style="' + syltpl.format(bgc) + syladd + '"'
        syl1 = ' style="' + syltpl.format(bgc1) + syladd1 + '"'
        syl2 = ' style="' + syltpl.format(bgc2) + syladd2 + '"'
        syln1 = ' style="' + syltpl.format(bgcn1) + '"'
        syln2 = ' style="' + syltpl.format(bgcn2) + '"'
        cls = ' class="even"' if i%2 == 0 else 'class="odd"'
        rs = ' rowspan="{}"'.format(len(idiffs)+2) if idiffs is not None else ''
        html += ('<tr style="color: #000;'
                 'border-bottom: 1px solid #ddd; border-top: 1px solid #ddd; border-collapse: collapse;">'
                 '<td {}>{}</td><td {}>{}</td><td {}>{}</td><td {}>{}</td><td {}>{}</td>'.format(
                     cls+rs+syln1, escape(idx1), cls+rs+syl1, escape(seq1),
                     cls+rs+syl, escape(code),
                     cls+rs+syl2, escape(seq2), cls+rs+syln2, escape(idx2), ))
        if idiffs is not None:
            html += '<td {}></td></tr>'.format(sylsep)
            si1 = si2 = 0
            for h, idiff in enumerate(idiffs):
                (icode, slice1, slice2) = idiff
                bgc = bgc1 = bgcn1 = bgc2 = bgcn2 = '#fff'
                syladd = syladd1 = syladd2 = ""
                efunc = escape
                if icode == '-':
                    slice2 = nonetoe(slice2)
                    bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#ffd7d5', '#ffebe9', '#ffd7d5', '#f5f7f8', '#f5f7f8')
                    syladd += 'font-weight: bold; color: #700;'
                    syladd1 += 'font-weight: bold; color: #700;'
                if icode == '+':
                    slice1 = nonetoe(slice1)
                    bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#ccffd8', '#f5f7f8', '#f5f7f8', '#e6ffec', '#ccffd8')
                    syladd += 'font-weight: bold; color: #040;'
                    syladd2 += 'font-weight: bold; color: #040;'
                if icode == '!':
                    bgc, bgcn1, bgc1, bgcn2, bgc2 = ('#f2e8ab', '#ffebe9', '#ffd7d5', '#e6ffec', '#ccffd8')
                    syladd += 'font-weight: bold; color: #330;'
                    syladd1 += 'font-weight: bold; color: #700;'
                    syladd2 += 'font-weight: bold; color: #040;'
                if icode == ' ' and truncate is not None:
                    efunc = lambda s: trunc(escape(s).strip(), int(truncate))
                syl = ' style="' + syltpl.format(bgc) + syladd + '"'
                syl1 = ' style="' + syltpl.format(bgc1) + syladd1 + '"'
                syl2 = ' style="' + syltpl.format(bgc2) + syladd2 + '"'
                syln1 = ' style="' + syltpl.format(bgcn1) + '"'
                syln2 = ' style="' + syltpl.format(bgcn2) + '"'
                sic = lambda si, size: '{}'.format(si) if size == 1 else '{}:{}'.format(si, si+size)
                html += '{}<td {}>{}<td {}>{}<td {}>{}</td><td {}>{}</td><td {}>{}</td><td {}>{}</td></tr>'.format(
                    '<tr style="color: #000;">',
                    sylsep, "",
                    syln1, sic(si1, len(slice1)) if slice1 is not None else '',
                    syl1, efunc(slice1),
                    syl, escape(icode),
                    syl2, efunc(slice2),
                    syln2, sic(si2, len(slice2)) if slice2 is not None else '',
                )
                si1 += len(slice1) if slice1 is not None else 0
                si2 += len(slice2) if slice2 is not None else 0
            html += '<tr><td {}></td></tr>'.format(sylsep)
        else:
            html += '<td {}></td></tr>'.format(sylsep)
    html += '</tbody></table>'
    return JupyterHTMLStr(html)


# filecmp.dircmp (ext_dircmp)
#  |-- left_list           [files or dirs]
#  | |-- left_only         [files or dirs]
#  | `-.  |-- (ext_left_only_dirs)         [dirs]
#  |   |  `-- (ext_left_only_files)        [files]
#  `-- right_list          [files or dirs]
#    |-- right_only        [files or dirs]
#    | |  |-- (ext_right_only_dirs)     [dirs]
#    `-+  `-- (ext_right_only_files)    [files]
#      |
#      `-- common          [files or dirs]
#        |-- common_dirs   [dirs] --> subdirs[common_dir]
#        |-- common_files  [files]
#        | |-- same_files  [files]
#        | |-- diff_files  [files]
#        | `-- funny_files [files]
#        `-- common_funny  [????]
#          |-- (ext_dirs_to_files) [dir  <-> file]
#          |-- (ext_files_to_dirs) [file <-> dir ]
#          `-- (ext_common_funny)  [????]

class ext_dircmp(filecmp.dircmp):

    def phase1(self): # Compute common names
        filecmp.dircmp.phase1(self)
        self.ext_left_only_dirs   = [x for x in self.left_only
                                     if os.path.isdir (os.path.join(self.left,  x))]
        self.ext_right_only_dirs  = [x for x in self.right_only
                                     if os.path.isdir (os.path.join(self.right, x))]
        self.ext_left_only_files  = [x for x in self.left_only
                                     if os.path.isfile(os.path.join(self.left,  x))]
        self.ext_right_only_files = [x for x in self.right_only
                                     if os.path.isfile(os.path.join(self.right, x))]


    def phase2(self): # Distinguish files, directories, funnies
        self.common_dirs = []
        self.common_files = []
        self.common_funny = []
        self.ext_dirs_to_files = []
        self.ext_files_to_dirs = []
        self.ext_common_funny = []

        for x in self.common:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)

            ok = 1
            try:
                a_stat = os.stat(a_path)
            except os.error:
                ok = 0
            try:
                b_stat = os.stat(b_path)
            except os.error:
                ok = 0

            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if a_type != b_type:
                    self.common_funny.append(x)
                    if   stat.S_ISDIR(a_type) and stat.S_ISREG(b_type):
                        self.ext_dirs_to_files.append(x)
                    elif stat.S_ISREG(a_type) and stat.S_ISDIR(b_type):
                        self.ext_files_to_dirs.append(x)
                    else:
                        self.ext_common_funny.append(x)
                elif stat.S_ISDIR(a_type):
                    self.common_dirs.append(x)
                elif stat.S_ISREG(a_type):
                    self.common_files.append(x)
                else:
                    self.common_funny.append(x)
                    self.ext_common_funny.append(x)
            else:
                self.common_funny.append(x)
                self.ext_common_funny.append(x)

    def phase3(self): # Find out differences between common files
        xx = filecmp.cmpfiles(self.left, self.right, self.common_files, shallow=0)
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self): # Find out differences between common subdirectories
        # A new dircmp object is created for each common subdirectory,
        # these are stored in a dictionary indexed by filename.
        # The hide and ignore properties are inherited from the parent
        self.subdirs = {}
        for x in self.common_dirs:
            a_x = os.path.join(self.left, x)
            b_x = os.path.join(self.right, x)
            self.subdirs[x]  = ext_dircmp(a_x, b_x, self.ignore, self.hide)

    def __getattr__(self, attr):
        methodmap = {'subdirs' : self.phase4,
                     'same_files' : self.phase3,
                     'diff_files' : self.phase3,
                     'funny_files' : self.phase3,
                     'common_dirs' : self.phase2,
                     'common_files' : self.phase2,
                     'common_funny' : self.phase2,
                     'ext_dirs_to_files' : self.phase2,
                     'ext_files_to_dirs' : self.phase2,
                     'ext_common_funny' : self.phase2,
                     'common' : self.phase1,
                     'left_only' : self.phase1,
                     'ext_left_only_dirs' : self.phase1,
                     'ext_left_only_files' : self.phase1,
                     'right_only' : self.phase1,
                     'ext_right_only_dirs' : self.phase1,
                     'ext_right_only_files' : self.phase1,
                     'left_list' : self.phase0,
                     'right_list' : self.phase0}
        if attr not in methodmap:
            raise AttributeError(attr)
        methodmap[attr]()
        return getattr(self, attr)

    def dirtree(self):
        left_dirset = set(self.ext_left_only_dirs  +
                          self.common_dirs         +
                          self.ext_dirs_to_files)
        left_fileset = set(self.ext_files_to_dirs    +
                           self.ext_left_only_files  +
                           self.same_files       +
                           self.diff_files       +
                           self.funny_files      +
                           self.ext_common_funny)
        right_dirset = set(self.ext_right_only_dirs +
                           self.common_dirs         +
                           self.ext_files_to_dirs)
        right_fileset = set(self.ext_dirs_to_files    +
                            self.ext_right_only_files +
                            self.same_files       +
                            self.diff_files       +
                            self.funny_files      +
                            self.ext_common_funny)

        left_list  = ([('d', left_dir)   for left_dir   in sorted(left_dirset)] +
                      [('f', left_file)  for left_file  in sorted(left_fileset)])
        right_list = ([('d', right_dir)  for right_dir  in sorted(right_dirset)] +
                      [('f', right_file) for right_file in sorted(right_fileset)])

        if len(left_list):
            last_left = left_list[-1]
            left_islast = False
        else:
            left_islast = None
        if len(right_list):
            last_right = right_list[-1]
            right_islast = False
        else:
            right_islast = None

        ftype = 'd'
        dirset = set(self.ext_left_only_dirs  +
                     self.ext_right_only_dirs +
                     self.common_dirs         +
                     self.ext_dirs_to_files   +
                     self.ext_files_to_dirs)
        for dirname in sorted(dirset):
            dircmpobj = None
            if   (dirname in self.ext_left_only_dirs or
                  dirname in self.ext_dirs_to_files):
                tag = '<'
            elif (dirname in self.ext_right_only_dirs or
                  dirname in self.ext_files_to_dirs):
                tag = '>'
            elif dirname in self.common_dirs:
                tag = ' '
                dircmpobj = self.subdirs[dirname]
            else:
                tag = '?'

            if (left_islast is not None and
                last_left[0] == ftype and
                last_left[1] == dirname): left_islast = True
            if (right_islast is not None and
                last_right[0] == ftype and
                last_right[1] == dirname): right_islast = True

            yield (ftype, tag, dirname, dircmpobj, left_islast, right_islast)

            if left_islast:  left_islast = None
            if right_islast: right_islast = None


        ftype = 'f'
        fileset = set(self.ext_dirs_to_files    +
                      self.ext_files_to_dirs    +
                      self.ext_left_only_files  +
                      self.ext_right_only_files +
                      self.same_files       +
                      self.diff_files       +
                      self.funny_files      +
                      self.ext_common_funny)
        for filename in sorted(fileset):
            if   (filename in self.ext_files_to_dirs or
                  filename in self.ext_left_only_files):
                tag = '<'
            elif (filename in self.ext_dirs_to_files or
                  filename in self.ext_right_only_files):
                tag = '>'
            elif filename in self.same_files:
                tag = ' '
            elif filename in self.diff_files:
                tag = '|'
            else:
                tag = '?'

            if (left_islast is not None and
                last_left[0] == ftype and
                last_left[1] == filename): left_islast = True
            if (right_islast is not None and
                last_right[0] == ftype and
                last_right[1] == filename): right_islast = True

            yield (ftype, tag, filename, None, left_islast, right_islast)

            if left_islast:  left_islast = None
            if right_islast: right_islast = None

        return


def formatdircmp(tag, head1, text1, head2, text2, width,
                 cont_mark1='^', cont_mark2='^', sep_mark='|',
                 withcolor=False):
    pwidth = ((strwidth(head1) + strwidth(sep_mark)) +
              (1 + strwidth(tag) + 1) +
              (strwidth(head2) + strwidth(sep_mark)))

    assert width >= pwidth
    textwidth = int((width - pwidth) / 2)

    text1_array = strwidthdiv(text1, textwidth)
    text2_array = strwidthdiv(text2, textwidth)

    for i in range(max(len(text1_array), len(text2_array))):
        line = ''
        if i != 0: head1 = cont_mark1
        if i != 0: head2 = cont_mark2

        try: ptext1 = text1_array[i]
        except(IndexError):
            ptext1 = ''
        try: ptext2 = text2_array[i]
        except(IndexError):
            ptext2 = ''

        line += head1
        line += sep_mark
        line += getcolor(withcolor, tag, 0, 0, isdircmp=True)
        line += ptext1
        line += getcolor(withcolor, tag, 0, 1, isdircmp=True)
        line += (max(textwidth - strwidth(ptext1), 0) * ' ' + '')
        if   i == 0:     line += (' ' + tag + ' ')
        elif tag == ' ': line += (' ' + ' ' + ' ')
        else:            line += (' ' + '^' + ' ')
        line += head2
        line += sep_mark
        line += getcolor(withcolor, tag, 1, 0, isdircmp=True)
        line += ptext2
        line += getcolor(withcolor, tag, 1, 1, isdircmp=True)
        yield line
    return

# 独自の形式で等幅フォントのターミナルで表示するための文字列の差分を返す。
def original_diff(differ, lines1, lines2, width, withcolor=False):
    r"""

    Example:

    >>> text1 = '''  1. Beautiful is better than ugly.
    ...   2. Explicit is better than implicit.
    ...   3. Simple is better than complex.
    ...   4. Complex is better than complicated.
    ... '''.splitlines(1)
    >>>
    >>> text2 = '''  1. Beautiful is better than ugly.
    ...   3.   Simple is better than complex.
    ...   4. Complicated is better than complex.
    ...   5. Flat is better than nested.
    ... '''.splitlines(1)
    >>>
    >>> differ = SidebysideDiffer(
    ...     linejunk=None,
    ...     charjunk=None,
    ...     cutoff=0.1,
    ...     fuzzy=0,
    ...     cutoffchar=False,
    ...     context=5)
    >>> diff = original_diff(differ, text1, text2, width=100)
    >>> for line in diff: print('\'' + line + '\'')
    '     1|  1. Beautiful is better than ugly.              1|  1. Beautiful is better than ugly.'
    '     2|  2. Explicit is better than implicit.    <       |'
    '     3|  3. Simple is better than complex.       |      2|  3.   Simple is better than complex.'
    '     4|  4. Complex is better than complicated.  |      3|  4. Complicated is better than complex.'
    '      |                                          >      4|  5. Flat is better than nested.'
    ''
    '[     ]      |    ++                                '
    '[ <-  ]     3|  3.   Simple is better than complex. '
    '[  -> ]     2|  3.   Simple is better than complex. '
    ''
    '[     ]      |          ++++ !                     ---- !  '
    '[ <-  ]     4|  4. Compl    ex is better than complicated. '
    '[  -> ]     3|  4. Complicated is better than compl    ex. '
    ''
    """

    lines1 = [expandtabs(line, tabsize=4) for line in lines1]
    lines2 = [expandtabs(line, tabsize=4) for line in lines2]

    for diff in differ.pretty_compare(lines1, lines2, width, withcolor):
        yield diff

def dircmp(dir1, dir2, enc_filepath='utf-8', recursive=False):
    r"""Compare directories."""
    dircmp   = ext_dircmp(dir1, dir2)
    dircmps  = [dircmp]
    dirtrees = [dircmp.dirtree()]
    heads1 = ['|']
    heads2 = ['|']
    while dirtrees:
        for dirtree in dirtrees[-1]:
            (ftype, tag, filepath, dircmpobj, left_islast, right_islast) = dirtree

            try: upath = filepath.decode(enc_filepath)
            except(AttributeError): upath = filepath

            if left_islast:
                heads1.pop()
                heads1.append('`')
            elif left_islast is None:
                heads1.pop()
                heads1.append(' ')
            if right_islast:
                heads2.pop()
                heads2.append('`')
            elif right_islast is None:
                heads2.pop()
                heads2.append(' ')

            head1 = '   '.join(heads1)
            head2 = '   '.join(heads2)

            if left_islast:
                heads1.pop()
                heads1.append(' ')
            if right_islast:
                heads2.pop()
                heads2.append(' ')

            cont_mark1 = '   '.join(heads1) + '   '
            cont_mark2 = '   '.join(heads2) + '   '

            if   ftype == 'd':
                upath += '/'
                mark = '-+ '
            elif ftype == 'f':
                mark = '-- '
            else: pass

            if tag == '<':
                text1 = upath
                text2 = ''
                head1 += mark
                head2 += '   '
            elif tag == '>':
                text1 = ''
                text2 = upath
                head1 += '   '
                head2 += mark
            else:
                text1 = upath
                text2 = upath

                if not recursive and dircmpobj is not None:
                    tag = '?'
                    head1 += '-+ '
                    head2 += '-+ '
                else:
                    head1 += '-- '
                    head2 += '-- '

            filepair = None

            if ftype == 'f' and tag == '|':
                path1 = os.path.join(dircmps[-1].left,  filepath)
                path2 = os.path.join(dircmps[-1].right, filepath)

                try: upath1 = path1.decode(enc_filepath)
                except(AttributeError): upath1 = path1
                try: upath2 = path2.decode(enc_filepath)
                except(AttributeError): upath2 = path2

                filepair = (upath1, upath2)

            yield (tag,
                   head1, text1, head2, text2,
                   cont_mark1, cont_mark2,
                   filepair)

            if recursive and dircmpobj is not None:
                dircmps.append(dircmpobj)
                dirtrees.append(dircmpobj.dirtree())
                heads1.append('|')
                heads2.append('|')
                break
        else:
            dircmps.pop()
            dirtrees.pop()
            heads1.pop()
            heads2.pop()

def parse_unidiff(diff):
    r"""Unified diff parser, takes a file-like object as argument.

    Example:

    >>> hg_diff = r'''diff -r dab26450e4b1 text2.txt
    ... --- a/text2.txt     Sun Dec 15 17:38:49 2013 +0900
    ... +++ b/text2.txt     Sun Dec 15 17:43:09 2013 +0900
    ... @@ -1,3 +1,3 @@
    ... -hoge
    ... +hogee
    ... +bar
    ...  foo
    ... -bar
    ... '''
    >>> diffs = parse_unidiff((line for line in hg_diff.splitlines()))
    >>> for (flag, diff) in diffs:
    ...     if flag: print(diff)
    ...     else:
    ...         for hunk in diff:
    ...             import pprint
    ...             pprint.pprint([s[1:] for s in hunk.source])
    ...             pprint.pprint([s[1:] for s in hunk.target])
    ...
    diff -r dab26450e4b1 text2.txt
    --- a/text2.txt     Sun Dec 15 17:38:49 2013 +0900
    +++ b/text2.txt     Sun Dec 15 17:43:09 2013 +0900
    ['hoge', 'foo', 'bar']
    ['hogee', 'bar', 'foo']
    >>>
    """
    import unidiff
    patches = unidiff.PatchSet(diff)  # , encoding=encoding)
    for patch in patches:
        
        if patch.patch_info:
            for line in patch.patch_info:
                yield (True, line)

        if patch.is_binary_file:
            continue

        if patch.source_file is not None:
            yield (True, '--- ' + patch.source_file)
        if patch.target_file is not None:
            yield (True, '+++ ' + patch.target_file)
        
        yield (False, patch)
    return

def parse_unidiff_and_original_diff(
        differ, udiffs, width, withcolor=False):
    r"""

    Example:

    >>> svn_diff = u'''Index: some.png
    ... ===================================================================
    ... Cannot display: file marked as a binary type.
    ... svn:mime-type = application/octet-stream
    ... Index: text1.txt
    ... ===================================================================
    ... --- text1.txt       (revision 1)
    ... +++ text1.txt       (working copy)
    ... @@ -1,4 +1,4 @@
    ...  1. Beautiful is better than ugly.
    ... -2. Explicit is better than implicit.
    ... -3. Simple is better than complex.
    ... -4. Complex is better than complicated.
    ... +3.   Simple is better than complex.
    ... +4. Complicated is better than complex.
    ... +5. Flat is better than nested.
    ... '''
    >>> differ = SidebysideDiffer(
    ...     linejunk=None, charjunk=None,
    ...     cutoff=0.1, fuzzy=0,
    ...     cutoffchar=False, context=5)
    >>> diff = parse_unidiff_and_original_diff(
    ...     differ,
    ...     (line for line in svn_diff.splitlines()),
    ...     width=100)
    >>> for line in diff: print('\'' + line + '\'')
    'Index: some.png'
    '==================================================================='
    'Cannot display: file marked as a binary type.'
    'svn:mime-type = application/octet-stream'
    'Index: text1.txt'
    '==================================================================='
    '--- text1.txt       (revision 1)'
    '+++ text1.txt       (working copy)'
    '     1|1. Beautiful is better than ugly.                1|1. Beautiful is better than ugly.'
    '     2|2. Explicit is better than implicit.      <       |'
    '     3|3. Simple is better than complex.         |      2|3.   Simple is better than complex.'
    '     4|4. Complex is better than complicated.    |      3|4. Complicated is better than complex.'
    '      |                                          >      4|5. Flat is better than nested.'
    ''
    '[     ]      |  ++                               '
    '[ <-  ]     3|3.   Simple is better than complex.'
    '[  -> ]     2|3.   Simple is better than complex.'
    ''
    '[     ]      |        ++++ !                     ---- ! '
    '[ <-  ]     4|4. Compl    ex is better than complicated.'
    '[  -> ]     3|4. Complicated is better than compl    ex.'
    ''
    >>>
    >>> hg_diff = u'''diff -r dab26450e4b1 some.png
    ... Binary file some.png has changed
    ... diff -r dab26450e4b1 text1.txt
    ... --- a/text1.txt     Sun Dec 15 17:38:49 2013 +0900
    ... +++ b/text1.txt     Sun Dec 15 17:43:09 2013 +0900
    ... @@ -1,4 +1,4 @@
    ...  1. Beautiful is better than ugly.
    ... -2. Explicit is better than implicit.
    ... -3. Simple is better than complex.
    ... -4. Complex is better than complicated.
    ... +3.   Simple is better than complex.
    ... +4. Complicated is better than complex.
    ... +5. Flat is better than nested.
    ... '''
    >>> differ = SidebysideDiffer(
    ...     linejunk=None, charjunk=None,
    ...     cutoff=0.1, fuzzy=0,
    ...     cutoffchar=False, context=5)
    >>> diff = parse_unidiff_and_original_diff(
    ...     differ,
    ...     (line for line in hg_diff.splitlines()),
    ...     width=100)
    >>> for line in diff: print('\'' + line + '\'')
    'diff -r dab26450e4b1 some.png'
    'Binary file some.png has changed'
    'diff -r dab26450e4b1 text1.txt'
    '--- a/text1.txt     Sun Dec 15 17:38:49 2013 +0900'
    '+++ b/text1.txt     Sun Dec 15 17:43:09 2013 +0900'
    '     1|1. Beautiful is better than ugly.                1|1. Beautiful is better than ugly.'
    '     2|2. Explicit is better than implicit.      <       |'
    '     3|3. Simple is better than complex.         |      2|3.   Simple is better than complex.'
    '     4|4. Complex is better than complicated.    |      3|4. Complicated is better than complex.'
    '      |                                          >      4|5. Flat is better than nested.'
    ''
    '[     ]      |  ++                               '
    '[ <-  ]     3|3.   Simple is better than complex.'
    '[  -> ]     2|3.   Simple is better than complex.'
    ''
    '[     ]      |        ++++ !                     ---- ! '
    '[ <-  ]     4|4. Compl    ex is better than complicated.'
    '[  -> ]     3|4. Complicated is better than compl    ex.'
    ''
    >>>
    """
    diffs = parse_unidiff(udiffs)
    for (flag, diff) in diffs:
        if flag: yield diff
        else:
            for hunk in diff:
                lines1 = [expandtabs(str(line)[1:], tabsize=4) for line in hunk.source_lines()]
                lines2 = [expandtabs(str(line)[1:], tabsize=4) for line in hunk.target_lines()]

                textlinediffs = []
                for diff in differ.pretty_compare(lines1, lines2, width, withcolor,
                    offset1=hunk.source_start - 1,
                    offset2=hunk.target_start - 1):
                    yield diff
    return

def getTerminalSize():
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])

def getdefaultencoding():
    defaultencoding = sys.getdefaultencoding()
    if defaultencoding == 'ascii': return 'utf8'
    return defaultencoding

def make_argparser():
    # オプション解析
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('file_or_dir_1', nargs='?', help='file or dir 1')
    parser.add_argument('file_or_dir_2', nargs='?', help='file or dir 2')

    parser.add_argument(
        '-y', '-s', '--side-by-side', action='store_true',
        help='output in two columns')

    # -fオプション: 差分を抽出した箇所以外のテキスト全体を表示する
    parser.add_argument('-f', '--full', action='store_true', default=False,
                        help='Fulltext diff (default False) (disable context option)')
    # -cオプション: 差分を抽出した箇所の前後の行数を指定する（デフォルトは前後5行）
    parser.add_argument('-c', '--context', metavar='NUM', type=int, default=5,
                        help='Set number of context lines (default 5)')

    # -wオプション: 差分表示時の最大の横幅を指定する（制限する）
    class CheckWidth(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if values <= 0:
                raise argparse.ArgumentError(self, 'set a larger number.')
            setattr(namespace, self.dest, values)
    parser.add_argument('-w', '--width', type=int, default=None, action=CheckWidth,
                        help='Set number of width  (default auto(or 130))')
    # -rオプション: ディレクトリ比較時にサブディレクトリが見つかった場合、再帰的に比較する
    parser.add_argument('-r', '--recursive', action='store_true', default=False,
                        help='Recursively compare any subdirectories found. (default False)'
                        ' (enable only compare directories)')
    class CheckRatio(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if not 0.0 <= values <= 1.0:
                raise argparse.ArgumentError(
                    self, 'set number in range (0.0 <= number <= 1.0 ).')
            setattr(namespace, self.dest, values)
    #
    class CheckRegexp(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            try: re.compile(values)
            except:
                raise argparse.ArgumentError(self, 'wrong regexp')
            setattr(namespace, self.dest, values)
    parser.add_argument('--linejunk', type=str, action=CheckRegexp,
                        help='linejunk')
    #
    parser.add_argument('--charjunk', type=str, action='store',
                        help='charjunk')
    # --cutoffオプション: 差分抽出時の行マージ判定割合を指定する（デフォルトは75%）
    parser.add_argument('--cutoff', metavar='RATIO', type=float, default=0.75,
                        action=CheckRatio,
                        help='Set number of cutoff ratio (default 0.75) (0.0<=ratio<=1.0)')
    # --fuzzyオプション: 差分抽出時のマージ適用調節割合を指定する（デフォルトは0.0%）
    parser.add_argument('--fuzzy', type=float, metavar='RATIO', default=0.0,
                        action=CheckRatio,
                        help='Set number of fuzzy matching ratio (default 0.0) (0.0<=ratio<=1.0)')
    # --cutoffcharオプション: 差分抽出時に文字の変更を分けて表示するかどうかを指定する
    # （デフォルトはFlase(分けない)）
    parser.add_argument('--cutoffchar', action='store_true', default=False,
                        help='Cutoff character in line diffs (default False)')

    class CheckCodec(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            try: values = codecs.lookup(values).name
            except(LookupError):
                raise argparse.ArgumentError(
                    self, 'LookupError: unknown encoding \'' + values + '\'')
            setattr(namespace, self.dest, values)
    # --enc-file1オプション: 左側のファイルを開く際のコーデックを指定する（デフォルトはutf-8）
    parser.add_argument('--enc-file1', metavar='ENCODING', type=str, default='utf-8',
                        action=CheckCodec,
                        help='Set encoding of leftside inputfile1 (default utf-8)')
    # --enc-file2オプション: 右側のファイルを開く際のコーデックを指定する（デフォルトはutf-8）
    parser.add_argument('--enc-file2', metavar='ENCODING', type=str, default='utf-8',
                        action=CheckCodec,
                        help='Set encoding of rightside inputfile2 (default utf-8)')
    # --enc-stdinオプション: Unified形式の差分を標準入力する際のコーデックを指定する（デフォルトはdefaultencoding）
    parser.add_argument('--enc-stdin', metavar='ENCODING', type=str, default=getdefaultencoding(),
                        action=CheckCodec,
                        help='Set encoding of standard input (default `defaultencoding`)')
    # --enc-stdoutオプション: 差分を標準出力する際のコーデックを指定する（デフォルトはdefaultencoding）
    parser.add_argument('--enc-stdout', metavar='ENCODING', type=str, default=getdefaultencoding(),
                        action=CheckCodec,
                        help='Set encoding of standard output (default `defaultencoding`)')
    # --enc-filepathオプション: ファイル名に使用されるコーデックを指定する（デフォルトはdefaultencoding）
    parser.add_argument('--enc-filepath', metavar='ENCODING', type=str, default=getdefaultencoding(),
                        action=CheckCodec,
                        help='Set encoding of filepath (default `defaultencoding`)')
    # --ignore-crlfオプション: 改行コードの違い（crとlf）を無視する
    parser.add_argument('--ignore-crlf', action='store_true', default=False,
                        help='Ignore carriage return (\'\\r\') and line feed (\'\\n\') (default False)')

    # --colorオプション: 色付き表示の指定（デフォルトはauto）
    parser.add_argument('--color', nargs='?', choices=colormodes.keys(),
                        metavar='WHEN', type=str, default='auto',
                        help='Show colored diff. --color is the same as --color=always.'
                        ' WHEN can be one of always, never, or auto. (default auto)')
    # --no-colorオプション: 色付き表示無効の指定
    parser.add_argument('--no-color', action='store_true', default=False,
                        help='Turn off colored diff. override color option if both. (default False)')
    # --withbgオプション: 色付き表示での背景色有りの指定
    parser.add_argument('--withbg', action='store_true', default=False,
                        help='Colored diff with background color. '
                        'It will be ignored if no-color option. (default False)')

    return parser 

def main():
    """main function"""

    parser = make_argparser()

    if __name__ == "__main__":
        # --testオプション: テストコードを実行
        parser.add_argument('--test', action='store_true', help='Test self')

    if __name__ == "__main__":
        parser.add_argument('--profile', action='store_true', help='Profile')

    # オプション解析を実行
    args = parser.parse_args()
    args._colormodes = colormodes

    if hasattr(args, 'test') and args.test:
        import doctest
        result = doctest.testmod(verbose=False)
        print(result)
        parser.exit(0 if result.failed == 0 else 1)

    if hasattr(args, 'profile') and args.profile:
        import profile
        pr = profile.Profile()
        ret = pr.runcall(uxdiff, args)
        pr.print_stats(sort=2)
        return ret

    # pdb.runcall(main)
    return uxdiff(args, parser)

def uxdiff(args, parser):

    file_or_dir1, file_or_dir2 = args.file_or_dir_1, args.file_or_dir_2
    # 必須引数の個数が所定と異なる場合は
    if file_or_dir1 is None and file_or_dir2 is None:
        pass
    elif file_or_dir1 is not None and file_or_dir2 is not None:
        pass
    else:
        # メッセージを表示して終了
        parser.error('Need to specify both a file1 and file2')

    context = args.context
    full = not args.full

    try: stdin_buffer = sys.stdin.buffer
    except(AttributeError):
        sys.stdin = codecs.getreader(args.enc_stdin)(sys.stdin) # python2.x
    else:
        sys.stdin = io.TextIOWrapper(stdin_buffer, encoding=args.enc_stdin) # python3.x

    try: stdout_buffer = sys.stdout.buffer
    except(AttributeError):
        sys.stdout = codecs.getwriter(args.enc_stdout)(sys.stdout) # python2.x
    else:
        sys.stdout = io.TextIOWrapper(stdout_buffer, encoding=args.enc_stdout) # python3.x

    if args.full:
        context = None
    else:
        context = args.context

    if args.linejunk != None:
        linejunk = lambda line: re.compile(args.linejunk).match(line) is not None
    else:
        linejunk = None

    if args.charjunk != None:
        charjunk = lambda char: char in args.charjunk
    else:
        charjunk = None

    if args.width is None:
        size = getTerminalSize()
        if size is not None:
            args.width = size[0]
        else:
            args.width = 130

    withcolor = True
    if args.no_color is True:
        withcolor = False
    else:
        if args.color is None or args._colormodes[args.color] is True:
            withcolor = True
        elif args._colormodes[args.color] is False:
            withcolor = False
        else:
            if not sys.stdout.isatty():
                withcolor = False

    if withcolor and args.withbg:
        global global_withbg
        global_withbg = True

    differ_class = UniLikeDiffer
    if args.side_by_side:
        differ_class = SidebysideDiffer

    # 差分を抽出
    differ = differ_class(
        linejunk=linejunk,
        charjunk=charjunk,
        cutoff=args.cutoff,
        fuzzy=args.fuzzy,
        cutoffchar=args.cutoffchar,
        context=context)

    cmpdir = False
    cmplist = []
    if file_or_dir1 is None:
        for line in parse_unidiff_and_original_diff(
                differ,
                sys.stdin,
                width=args.width,
                withcolor=withcolor):
            print(line)
    elif os.path.isdir(file_or_dir1) and os.path.isdir(file_or_dir2):
        # diff [DIR] and [DIR]
        cmpdir = True

        for line in formatdircmp(' ',
                                 '', file_or_dir1 + '/', '', file_or_dir2 + '/',
                                 args.width,
                                 cont_mark1='', cont_mark2='', sep_mark='',
                                 withcolor=withcolor):
            print(line)

        for result in dircmp(file_or_dir1, file_or_dir2,
                             args.enc_filepath, args.recursive):
            (tag,
            head1, text1,
            head2, text2,
            cont_mark1, cont_mark2,
            filepair) = result

            for line in formatdircmp(tag,
                                     head1, text1, head2, text2,
                                     args.width,
                                     cont_mark1=cont_mark1,
                                     cont_mark2=cont_mark2,
                                     sep_mark='',
                                     withcolor=withcolor):
                print(line)
            if filepair is not None:
                cmplist.append(filepair)
        print('')
    else:
        try: file_or_dir1 = file_or_dir1.decode(args.enc_filepath) # python2.x
        except(AttributeError): pass # python3.x
        try: file_or_dir2 = file_or_dir2.decode(args.enc_filepath) # python2.x
        except(AttributeError): pass # python3.x

        if   os.path.isdir(file_or_dir1):
            # diff [DIR/FILE] and [FILE]
            cmplist = [(os.path.join(file_or_dir1, os.path.basename(file_or_dir2)), file_or_dir2)]
        elif os.path.isdir(file_or_dir2):
            # diff [FILE] and [DIR/FILE]
            cmplist = [(file_or_dir1, os.path.join(file_or_dir2, os.path.basename(file_or_dir1)))]
        else:
            # diff [FILE] and [FILE]
            cmplist = [(file_or_dir1, file_or_dir2)]

    label = []

    for file1, file2 in cmplist:

        # ラベルが-Lオプションで明示的に指定されていなければ、
        # ファイル名をラベルとして使用する
        if len(label) == 0: label.append(file1)
        if len(label) == 1: label.append(file2)

        is_text_file1 = None
        is_text_file2 = None

        if cmpdir:
            label[0] = file1
            label[1] = file2

            is_text_file1 = is_text(file1)
            is_text_file2 = is_text(file2)

            if not (is_text_file1 and is_text_file2):
                if is_text_file1: filetype1 = 'Text'
                else:             filetype1 = 'Binary'
                if is_text_file2: filetype2 = 'Text'
                else:             filetype2 = 'Binary'
            else:
                filetype1 = args.enc_file1
                filetype2 = args.enc_file2
        else:
            try: label[0] = label[0].decode(args.enc_filepath) # python2.x
            except(AttributeError): pass # python3.x
            try: label[1] = label[1].decode(args.enc_filepath) # python2.x
            except(AttributeError): pass # python3.x

            is_text_file1 = True
            is_text_file2 = True

            filetype1 = args.enc_file1
            filetype2 = args.enc_file2

        print('--- ' + label[0] + ' (' + filetype1 + ')')
        print('+++ ' + label[1] + ' (' + filetype2 + ')')

        if not (is_text_file1 and is_text_file2):
            print('Files ' + file1 + ' and ' + file2 + ' differ')
            print('')
            continue

        # 入力ファイルを開く
        lines1 = None
        lines2 = None
        try:
            # for Python3.x
            # lines1 = open(file1, 'r', encoding=args.enc_file1)
            # lines2 = open(file2, 'r', encoding=args.enc_file2)
            # for Python2.x
            lines1 = codecs.open(file1, 'r', encoding=args.enc_file1).readlines()
            lines2 = codecs.open(file2, 'r', encoding=args.enc_file2).readlines()
        # for Python2.x
        except IOError:
            if lines1 is None:
                filename = file1
            else:
                filename = file2
            print('[Errno 2] No such file or directory: \'' + filename + '\'')
            return 1
        except UnicodeDecodeError:
            if lines1 is None:
                filename = file1
                encoding_text = args.enc_file1
                optionname = '--enc-file1'
            else:
                filename = file2
                encoding_text = args.enc_file2
                optionname = '--enc-file2'
            print('\'' + filename  + '\' is not encoding by \'' + encoding_text + '\'')
            print('Set correct encoding of \'' + filename + '\' by ' + optionname + ' option')
            if cmpdir:
                print('')
                continue
            else:
                return 1
        # for Python3.x
        # except IOError as error:
        #     print(str(error))
        # except UnicodeDecodeError as error:
        #     print(str(error))

        if args.ignore_crlf:
            lines1 = [line.rstrip('\r\n') for line in lines1]
            lines2 = [line.rstrip('\r\n') for line in lines2]

        # expandtabsは幅広文字に対応していないので自前で対処する
        # 以下のコードを試せば分かる
        # unicodestr = u'aあ\tb'
        # print(unicodestr.expandtabs(8).encode('sjis'))
        # print(unicodestr.encode('sjis'))

        diff = original_diff(
            differ,
            lines1, lines2,
            width=args.width,
            withcolor=withcolor)

        for line in diff: print(line)
    return 0

if __name__ == "__main__":
    sys.exit(main())
