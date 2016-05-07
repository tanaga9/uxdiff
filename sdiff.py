#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
#!/usr/bin/env python2.6
#!/usr/bin/env python3.0
#!/usr/bin/env jython
#!/usr/bin/env C:\Python26\python
#!/usr/bin/env C:\jython2.5.1\bin\jython

"""
Whats sdiff.py
==============
Compare two text files; generate the resulting delta.

License
=======
PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
"""

__author__ =  'Tanaga'
__version__=  '1.1.0 beta'


# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
# 
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
# ("PSF"), and the Individual or Organization ("Licensee") accessing and
# otherwise using this software ("Python") in source or binary form and
# its associated documentation.
# 
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby
# grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
# analyze, test, perform and/or display publicly, prepare derivative works,
# distribute, and otherwise use Python alone or in any derivative version,
# provided, however, that PSF's License Agreement and PSF's notice of copyright,
# i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 Python
# Software Foundation; All Rights Reserved" are retained in Python alone or in any
# derivative version prepared by Licensee.
# 
# 3. In the event Licensee prepares a derivative work that is based on
# or incorporates Python or any part thereof, and wants to make
# the derivative work available to others as provided herein, then
# Licensee hereby agrees to include in any such work a brief summary of
# the changes made to Python.
# 
# 4. PSF is making Python available to Licensee on an "AS IS"
# basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
# IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
# DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
# FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
# INFRINGE ANY THIRD PARTY RIGHTS.
# 
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
# FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
# A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
# OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
# 
# 6. This License Agreement will automatically terminate upon a material
# breach of its terms and conditions.
# 
# 7. Nothing in this License Agreement shall be deemed to create any
# relationship of agency, partnership, or joint venture between PSF and
# Licensee.  This License Agreement does not grant permission to use PSF
# trademarks or trade name in a trademark sense to endorse or promote
# products or services of Licensee, or any third party.
# 
# 8. By copying, installing or otherwise using Python, Licensee
# agrees to be bound by the terms and conditions of this License
# Agreement.


import sys, difflib, optparse, unicodedata, re, codecs, doctest
# import pprint, pdb, profile

import filecmp
import os, stat

import itertools
try:   itertools.filterfalse
except(AttributeError):
    itertools.filterfalse = itertools.ifilterfalse

# siff.pyとは
# ===========
# 2つのテキストファイルの差分を取り、人間にとって分かりやすい比較形式で表示する。
# 差分取得結果は等幅フォントを表示するターミナル上で直接表示できる。
# またテキスト差分取得をサポートするモジュールを提供する
#
# ライセンス
# ==========
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2


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


# filecmp.dircmp
#  |-- left_only       [files, dirs]
#  | `-- left_list     [files, dirs] - hide - ignore
#  |-- right_only      [files, dirs]
#  | `-- right_list    [files, dirs] - hide - ignore
#  `-- common          [files, dirs]
#    |-- common_dirs   [dirs] --> subdirs
#    |-- common_files  [files]
#    | |-- same_files  [files]
#    | |-- diff_files  [files]
#    | `-- funny_files [files]
#    `-- common_funny  [????]

class dircmp(filecmp.dircmp):
    def __init__(self, a, b, ignore=None, hide=None): # Initialize
        filecmp.dircmp.__init__(self, a, b, ignore, hide)
        self.left_only_dirs   = [x for x in self.left_only  if os.path.isdir (os.path.join(self.left, x))]
        self.left_only_files  = [x for x in self.left_only  if os.path.isfile(os.path.join(self.left, x))]
        self.left_list_dirs   = [x for x in self.left_list  if os.path.isdir (os.path.join(self.left, x))]
        self.left_list_files  = [x for x in self.left_list  if os.path.isfile(os.path.join(self.left, x))]
        self.right_only_dirs  = [x for x in self.right_only if os.path.isdir (os.path.join(self.right, x))]
        self.right_only_files = [x for x in self.right_only if os.path.isfile(os.path.join(self.right, x))]
        self.right_list_dirs  = [x for x in self.right_list if os.path.isdir (os.path.join(self.right, x))]
        self.right_list_files = [x for x in self.right_list if os.path.isfile(os.path.join(self.right, x))]
        pass
    
    def dic_dirs(self):
        dic = {}
        for x in self.left_only_dirs:   dic[x] = 'left_only_dir'
        for x in self.right_only_dirs:  dic[x] = 'right_only_dir'
        for x in self.common_dirs:      dic[x] = 'common_dir'
        for x in self.common_funny:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)
            
            ok = True
            try: a_stat = os.stat(a_path)
            except os.error: ok = False
            try: b_stat = os.stat(b_path)
            except os.error: ok = False
            
            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if   stat.S_ISDIR(a_type) and stat.S_ISREG(b_type):
                    dic[x] = 'common_funny_dir_to_file'
                elif stat.S_ISREG(a_type) and stat.S_ISDIR(b_type):
                    dic[x] = 'common_funny_file_to_dir'
                else: pass
            else: pass
            pass
        
        return dic
    
    def dic_files(self):
        dic = {}
        for x in self.left_only_files:  dic[x] = 'left_only_file'
        for x in self.right_only_files: dic[x] = 'right_only_file'
        for x in self.same_files:       dic[x] = 'same_file'
        for x in self.diff_files:       dic[x] = 'diff_file'
        for x in self.funny_files:      dic[x] = 'funny_file'
        for x in self.common_funny:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)
            
            ok = True
            try: a_stat = os.stat(a_path)
            except os.error: ok = False
            try: b_stat = os.stat(b_path)
            except os.error: ok = False
            
            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if   stat.S_ISDIR(a_type) and stat.S_ISREG(b_type):
                    dic[x] = 'common_funny_dir_to_file'
                elif stat.S_ISREG(a_type) and stat.S_ISDIR(b_type):
                    dic[x] = 'common_funny_file_to_dir'
                else: dic[x] = 'common_funny'
            else: dic[x] = 'common_funny'
            pass
        
        return dic
    
    def tree(self, recursive=True):
        print(self.left.ljust(50) + ''.ljust(5) + self.right)
        return self._tree(recursive)
    
    def _tree_only_left_right(self, which, ppath, prefix_left, prefix_right):
        dic_dirs  = {}
        dic_files = {}
        
        sub_list = list(itertools.filterfalse((self.hide+self.ignore).__contains__,
                                              os.listdir(ppath)))
        for x in sub_list:
            path = os.path.join(ppath, x)
            try: path_stat = os.stat(path)
            except: dic_files[x] = 'only_funny'
            else:
                path_type = stat.S_IFMT(path_stat.st_mode)
                if   stat.S_ISDIR(path_type): dic_dirs[x]  = 'only_funny_dir'
                elif stat.S_ISREG(path_type): dic_files[x] = 'only_funny_file'
                else: dic_files[x] = 'only_funny_file'
                pass
            pass
        
        dirs = dic_dirs
        for i, key in enumerate(sorted(dirs.keys())):
            if   which == 'left':
                left = '|-- ' + key + '/'
                right = ''
                flag = '<'
                subprefix_left  = prefix_left + '| '
                subprefix_right = prefix_right
            elif which == 'right':
                left = ''
                right = '|-- ' + key + '/'
                flag = '>'
                subprefix_left  = prefix_left
                subprefix_right = prefix_right + '| '
                pass
            print((prefix_left + left).ljust(50) + flag.ljust(5) + (prefix_right+ right))
            self._tree_only_left_right(which, os.path.join(ppath, key),
                                       subprefix_left, subprefix_right)
            pass
        
        files = dic_files
        for i, key in enumerate(sorted(files.keys())):
            if   which == 'left':
                left = '|-- ' + key
                right = ''
                flag = '<'
            elif which == 'right':
                left = ''
                right = '|-- ' + key
                flag = '>'
                pass
            print((prefix_left + left).ljust(50) + flag.ljust(5) + (prefix_right+ right))
            pass
        
        return
    
    def _tree(self, recursive=False, prefix='', diff_file_list=None):
        if diff_file_list == None: diff_file_list = []
        
        line = '|'
        dirs = self.dic_dirs()
        for i, key in enumerate(sorted(dirs.keys())):
            subdircmp = None
            subdir_only = None
            if   (dirs[key] == 'left_only_dir' or
                  dirs[key] == 'common_funny_dir_to_file'):
                left  = '|-- ' + key + '/'
                right = '|'
                flag  = '<'
                if recursive: subdir_only = 'left'
                pass
            elif (dirs[key] == 'right_only_dir' or
                  dirs[key] == 'common_funny_file_to_dir'):
                left  = '|'
                right = '|-- ' + key + '/'
                flag  = '>'
                if recursive: subdir_only = 'right'
                pass
            elif dirs[key] == 'common_dir':
                left  = '|-- ' + key + '/'
                right = '|-- ' + key + '/'
                if recursive:
                    a_x = os.path.join(self.left, key)
                    b_x = os.path.join(self.right, key)
                    subdircmp = dircmp(a_x, b_x, self.ignore, self.hide)
                    flag  = ' '
                else: flag  = '?'
                pass
            else: raise ''
            print((prefix + left).ljust(50) + flag.ljust(5) + (prefix + right))
            
            if subdircmp != None:
                diff_file_list += subdircmp._tree(recursive=True, prefix=prefix+'| ')
                pass
            elif subdir_only != None:
                if   subdir_only == 'left':
                    x = os.path.join(self.left,  key)
                elif subdir_only == 'right':
                    x = os.path.join(self.right, key)
                    pass
                self._tree_only_left_right(subdir_only, x,
                                           prefix_left=prefix+'| ',
                                           prefix_right=prefix+'| ')
                pass
            pass
        
        files = self.dic_files()
        for i, key in enumerate(sorted(files.keys())):
            if   (files[key] == 'left_only_file' or
                  files[key] == 'common_funny_file_to_dir'):
                left  = '|-- ' + key
                right = '|'
                flag  = '<'
            elif (files[key] == 'right_only_file' or
                  files[key] == 'common_funny_dir_to_file'):
                left  = '|'
                right = '|-- ' + key
                flag  = '>'
            elif files[key] == 'same_file':
                left  = '|-- ' + key
                right = '|-- ' + key
                flag  = ' '
            elif files[key] == 'diff_file':
                left  = '|-- ' + key
                right = '|-- ' + key
                flag  = '|'
                diff_file_list.append((os.path.join(self.left, key),
                                       os.path.join(self.right, key)))
            elif files[key] == 'funny_file':
                left  = '|-- ' + key
                right = '|-- ' + key
                flag  = '?'
            elif files[key] == 'common_funny':
                left  = '|-- ' + key
                right = '|-- ' + key
                flag  = '?'
            else: raise ''
            print((prefix + left).ljust(50) + flag.ljust(5) + (prefix + right))
            pass
        return diff_file_list
    
    pass


# テキスト差分取得クラス
# 内部処理にdifflibのSequenceMatcherクラスを使用している
class Differ:
    r"""Differ is a class for comparing sequences of lines of text, and
    producing human-readable differences or deltas.
    
    Differ uses SequenceMatcher both to compare sequences of lines,
    and to compare sequences of characters within similar (near-matching) lines.
    
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
    >>> d = Differ()
    >>>
    >>> result = list(d.compare(text1, text2))
    >>>
    >>> import pprint
    >>> pprint.pprint(result, width=120)
    [((' ', 0, '  1. Beautiful is better than ugly.\n', 0, '  1. Beautiful is better than ugly.\n'), None),
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
     None]
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
    def compare(self, text1, text2):
        r"""
        Compare two sequences of lines; generate the resulting delta.
        
        Example:
        
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
        >>> import pprint
        >>>
        >>> pprint.pprint(list(Differ().compare(text1, text2)), width=100)
        [(('>', None, None, 0, 'ore\n'), None),
         (('<', 0, 'one\n', None, None), None),
         (('<', 1, 'two\n', None, None), None),
         (('|', 2, 'three\n', 1, 'tree\n'), [(' ', 't', 't'), ('-', 'h', None), (' ', 'ree\n', 'ree\n')]),
         (('>', None, None, 2, 'emu\n'), None),
         None]
        
        # like sdiff
        >>> pprint.pprint(list(Differ(cutoff=0, fuzzy=1).compare(text1, text2)), width=100)
        [(('|', 0, 'one\n', 0, 'ore\n'), [(' ', 'o', 'o'), ('!', 'n', 'r'), (' ', 'e\n', 'e\n')]),
         (('|', 1, 'two\n', 1, 'tree\n'), [(' ', 't', 't'), ('!', 'wo', 'ree'), (' ', '\n', '\n')]),
         (('|', 2, 'three\n', 2, 'emu\n'),
          [('-', 'thr', None), (' ', 'e', 'e'), ('!', 'e', 'mu'), (' ', '\n', '\n')]),
         None]
         
        """
        
        # SequenceMatcherのインスタンスを生成する
        cruncher = difflib.SequenceMatcher(self.linejunk, text1, text2)
        
        # コンテキスト差分オプションがNoneでない場合は
        if self.context != None:
            # get_grouped_opcodesを使う
            opcodes = cruncher.get_grouped_opcodes(self.context)
        else:
            # get_opcodesを使う、ただしget_grouped_opcodesとインタフェースを
            # 合わせるために呼び出した後1枚リストをかぶせる
            opcodes = [cruncher.get_opcodes()]
        
        # 差分の纏まりのグループごとにループする
        for opcode in opcodes:
            # 差分の纏まりごとにループする
            for (tag,
                 text1_low, text1_high,
                 text2_low, text2_high) in opcode:
                # タグが変更の場合は
                if   tag == 'replace':
                    # さらにその変更の纏まり（複数行）のなかから、
                    # もっともマッチした行を検知し、その前後で
                    # 再びもっともマッチした行を検知し、その前後で・・・
                    # という再帰処理を行い、もっとも見た目が良い前後比較を作成する
                    gen = self._fancy_replace(text1, text1_low, text1_high,
                                              text2, text2_low, text2_high)
                    # ジェネレータを受け取るので要素を生成してyieldする
                    for line in gen:
                        yield line
                # タグが削除の場合は
                elif tag == 'delete':
                    # 削除分の行を個別に生成して返す
                    # 削除のタグは'<'とし、必要のない情報についてはNoneで返す
                    for num1 in range(text1_low, text1_high):
                        yield (('<', num1, text1[num1], None, None), None)
                # タグが追加の場合は
                elif tag == 'insert':
                    # 追加分の行を個別に生成して返す
                    # 追加のタグは'>'とし、必要のない情報についてはNoneで返す
                    for num2 in range(text2_low, text2_high):
                        yield (('>', None, None, num2, text2[num2]), None)
                # タグが一致の場合は
                elif tag == 'equal':
                    # 互いの行数が一致することをassertで確認する
                    assert text1_high - text1_low == text2_high - text2_low
                    # 一致分の行を個別に生成して返す
                    # 一致のタグは' 'とし、必要のない情報についてはNoneで返す
                    for num1, num2 in zip(range(text1_low, text1_high),
                                          range(text2_low, text2_high)):
                        yield ((' ', num1, text1[num1], num2, text2[num2]), None)
                # その他のタグを受け取った場合は
                else:
                    # 予定外なので例外を飛ばす
                    raise ValueError('unknown tag \'' + tag + '\'')
            
            # コンテキストの終わりをあらわすNoneを返す
            yield None
        return
    
    # 1ブロックの線をもう一つと入れ替えるとき、
    # *similar*線を求めてブロックを捜してください;
    # 最もあっている一組（あるとしても）が同期点として使われます、
    # そして、ライン内違い採点は類似した一組の上でされます。
    # しばしばそれの価値があるが、たくさんの仕事。
    def _fancy_replace(self,
                       text1, text1_low, text1_high,
                       text2, text2_low, text2_high):
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
        
        >>> #pprint.pprint(list(Differ().compare(text1, text2)), width=100)
        
        >>> results = Differ()._fancy_replace(text1, 0, 1,
        ...                                   text2, 0, 1)
        >>> pprint.pprint(list(results))
        [(('<', 0, 'teststring\n', None, None), None),
         (('>', None, None, 0, 'poststream\n'), None)]
        
        >>> results = Differ(cutoff=0, fuzzy=1)._fancy_replace(text1, 0, 1,
        ...                                                    text2, 0, 1)
        >>> pprint.pprint(list(results))
        [(('|', 0, 'teststring\n', 0, 'poststream\n'),
          [('!', 'te', 'po'),
           (' ', 'ststr', 'ststr'),
           ('!', 'ing', 'eam'),
           (' ', '\n', '\n')])]
        
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
        equal_text1_pos, equal_text2_pos = None, None
        
        # search for the pair that matches best without being identical
        # (identical lines must be junk lines, & we don't want to synch up
        # on junk -- unless we have to)
        # まったく同一ではなく、かつ最もマッチする一組をサーチする
        # （同一の文字列はジャンク文字列でなければならない、
        # 　特別そうしたい場合以外は、ジャンクで同期すべきではない）
        
        # text2について繰り返し処理する
        for text2_pos in range(text2_low, text2_high):
            # 取得したtext2の1行をSequenceMatcherにセットする
            cruncher.set_seq2(text2[text2_pos])
            # text1について繰り返し処理する
            for text1_pos in range(text1_low, text1_high):
                # 取得したtext1の1行とtext2の1行が完全一致する場合は
                if text1[text1_pos] == text2[text2_pos]:
                    # すでに完全一致ペアが見つかって居ない場合は
                    if equal_text1_pos is None:
                        # 今回のペアを最初の完全一致ペアとして記憶する
                        equal_text1_pos = text1_pos
                        equal_text2_pos = text2_pos
                    # このペアでやるべきことは何も無いので次のループへ
                    continue
                
                # 取得したtext1の1行をSequenceMatcherにセットする
                cruncher.set_seq1(text1[text1_pos])
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
                    best_i = text1_pos
                    best_j = text2_pos
        
        # ------------------------------------------------------------
        
        # ベストマッチのマッチ率がcutoffを超えていない場合は
        if not best_ratio > self.cutoff:
            # no non-identical "pretty close" pair
            # 『同一でない「かなり近い」ペア』が無い
            
            # 同一のペアも無い場合は
            if equal_text1_pos is None:
                # no identical pair either -- treat it as a straight replace
                # 単純に完全に置き換えられた文字列の集まりとする
                # '|'が存在せず、'>'および'<'、もしくは'>'および'<'
                # の集まりとする。
                # どちらが採用されるかはそれぞれの行数によって決まる
                # 行が少ないほうが先に返される。
                
                # dump the shorter block first -- reduces the burden on short-term
                # memory if the blocks are of very different sizes
                # 最初により少ない行数を処理する
                # これは行数非常に異なるサイズの場合に、メモリ上の負荷を減らす効果がある
                
                # text2のほうがtext1より行数が少ない場合は
                if text2_high - text2_low < text1_high - text1_low:
                    # text2について全行を'>'としてyieldする
                    for num2 in range(text2_low, text2_high):
                        yield (('>', None, None, num2, text2[num2]), None)
                    # text1について全行を'<'としてyieldする
                    for num1 in range(text1_low, text1_high):
                        yield (('<', num1, text1[num1], None, None), None)
                # text1のほうがtext2より行数が少ない場合は
                else:
                    # text1について全行を'<'としてyieldする
                    for num1 in range(text1_low, text1_high):
                        yield (('<', num1, text1[num1], None, None), None)
                    # text2について全行を'>'としてyieldする
                    for num2 in range(text2_low, text2_high):
                        yield (('>', None, None, num2, text2[num2]), None)
                return
            # no close pair, but an identical pair -- synch up on that
            # 『同一でない「かなり近い」ペア』は無いが、
            # 同一のペアがあるので、それで同期を取る
            best_i = equal_text1_pos
            best_j = equal_text2_pos
            best_ratio = 1.0
        else:
            # there's a close pair, so forget the identical pair (if any)
            # 『同一でない「かなり近い」ペア』が有る。
            # そのため、同一のペアを忘れる（たとえあるとしても）
            equal_text1_pos = None
        
        # ------------------------------------------------------------
        
        # a[best_i] very similar to b[best_j]; equal_text1_pos is None iff they're not
        # identical
        # この時点ではtext1[best_i]とtext2[best_j]は最適なペア（同一であるか
        # もしくは非常に似ているペア）となっている
        # 同一のペアである場合は、equal_text1_posはNoneではない
        # 非常に似ているペアの場合は、equal_text1_posはNoneとなっている
        
        # pump out diffs from before the synch point
        # 同期点（最適なペア）で区切った場合の前半に対して
        # 再帰的に同じ処理を行う（前半がなくなるまで続く）
        for line in self._fancy_helper(text1, text1_low, best_i,
                                       text2, text2_low, best_j):
            yield line
        
        # do intraline marking on the synch pair
        # 最適なペアについて行内差分を取得する
        text1_elt = text1[best_i]
        text2_elt = text2[best_j]
        
        # 非常に似ているペアの場合は（同一のペアでない場合は）
        if equal_text1_pos is None:
            # pump out a '-', '?', '+', '?' quad for the synched lines
            # 同期する文字列に対して判定を行い、'!' '-' '+' ' ' を設定する
            #   * '!' : 変更
            #   * '-' : 削除
            #   * '+' : 追加
            #   * ' ' : 同一
            line_tags = ''
            # SequenceMatcherを使用して差分を取得する
            cruncher.set_seqs(text1_elt, text2_elt)
            
            linediff_list = []
            # 差分をグループごとに取得
            for (tag,
                 text1_i1, text1_i2,
                 text2_j1, text2_j2) in cruncher.get_opcodes():
                
                # グループ内のそれぞれの文字数を記憶する
                la = text1_i2 - text1_i1
                lb = text2_j2 - text2_j1
                
                text1_elta = text1_elt[text1_i1:text1_i2]
                text2_elta = text2_elt[text2_j1:text2_j2]
                
                # 変更の場合
                if   tag == 'replace':
                    # 変更した文字をすべて同期して'!'で返すか、
                    # 個別に'-'および'+'で返すかを判定する
                    # （ratio()は0であることが確定しているので計算しない）
                    # （メモリの負荷はそれほど考慮しなくてよいので'+'および'-'では
                    # 　表示しない）
                    if self.cutoffchar:
                        # 個別に'-'および'+'で表示する
                        linediff_list.append(('-', text1_elta, None))
                        linediff_list.append(('+', None, text2_elta))
                    else:
                        # すべて同期して'!'で表示する
                        linediff_list.append(('!', text1_elta, text2_elta))
                # 削除の場合
                elif tag == 'delete': linediff_list.append(('-', text1_elta, None))
                # 追加の場合
                elif tag == 'insert': linediff_list.append(('+', None, text2_elta))
                # 同一の場合
                elif tag == 'equal': linediff_list.append((' ', text1_elta, text2_elta))
                # その他のタグを受け取った場合は
                else:
                    # 予定外なので例外を飛ばす
                    raise ValueError('unknown tag \'' + tag + '\'')
            yield (('|', best_i, text1_elt, best_j, text2_elt), linediff_list)
        else:
            # the synch pair is identical
            # ペアは同一
            yield ((' ', best_i, text1_elt, best_j, text2_elt), None)
        
        # pump out diffs from after the synch point
        # 同期点（最適なペア）で区切った場合の後半に対して
        # 再帰的に同じ処理を行う（後半がなくなるまで続く）
        for line in self._fancy_helper(text1, best_i+1, text1_high,
                                       text2, best_j+1, text2_high):
            yield line
        
        return
    
    # _fancy_replace()内から分割点の前半と後半の2回再帰的に
    # 呼び出される際に使用される関数
    def _fancy_helper(self,
                      text1, text1_low, text1_high,
                      text2, text2_low, text2_high):
        g = []
        # text1が存在する
        if text1_low < text1_high:
            # text2が存在する
            if text2_low < text2_high:
                # text1とtext2が両方存在するので
                # _fancy_replace()を再帰的に呼び出す
                g = self._fancy_replace(text1, text1_low, text1_high,
                                        text2, text2_low, text2_high)
                # イテレータが返るのでそのままyieldする
                for line in g:
                    yield line
            else:
                # text1が存在してtext2が無いので、
                # text1について'<'で返す
                for num1 in range(text1_low, text1_high):
                    yield (('<', num1, text1[num1], None, None), None)
        # text2が存在する
        elif text2_low < text2_high:
            # text2が存在してtext1が無いので、
            # text2について'>'で返す
            for num2 in range(text2_low, text2_high):
                yield (('>', None, None, num2, text2[num2]), None)
        return
    
    # 差分についてプレーンテキストでフォーマッティングを行う関数
    # （行内差分についてはサポートしていない）
    @staticmethod
    def formattext(tag, num1, text1, num2, text2, width):
        """
        
        Example:
        
        >>> Differ.formattext('|', 1, 'aaa', 2, 'bbb', 80)
        ['     2|aaa                             |      3|bbb']
        
        >>> Differ.formattext('|', 1, 'aaa', 2, 'bbb', 60)
        ['     2|aaa                   |      3|bbb']
        
        >>> Differ.formattext(' ', 1, 'aaa', 2, 'aaa', 80)
        ['     2|aaa                                    3|aaa']
        
        >>> Differ.formattext('<', 1, 'aaa', None, None, 80)
        ['     2|aaa                             <       |']
        
        >>> Differ.formattext('>', None, None, 2, 'bbb', 80)
        ['      |                                >      3|bbb']
        
        >>> import pprint
        >>> pprint.pprint(Differ.formattext('>',
        ...                                 1, 'a' * 80,
        ...                                 2, 'b' * 30, 80))
        ['     2|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa >      3|bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
         '     ^|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ^       |',
         '     ^|aaaaaaaaaaaaaaaaaa              ^       |']
        """
        
        assert width >= (6 + 1 + 2) + (1 + 1 + 1) + (6 + 1 + 2)
        textwidth = (width - ((6 + 1 + 0) + (1 + 1 + 1) + (6 + 1 + 0))) / 2
        
        lines = []
        line = ''
        
        if num1  == None: num1  = ''
        if num2  == None: num2  = ''
        if text1 == None: text1 = ''
        if text2 == None: text2 = ''
        
        text1 = text1.rstrip('\r\n')
        text2 = text2.rstrip('\r\n')
        
        text1 = text1.replace('\t', ' ')
        text2 = text2.replace('\t', ' ')
        
        text1_array = strwidthdiv(text1, textwidth)
        text2_array = strwidthdiv(text2, textwidth)
        
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
            
            # (6 + 1 + x) + (1 + 1 + 1) + (6 + 1 + y)
            line += (pnum1.rjust(6))
            line += ('|')
            line += (ptext1)
            line += (max(textwidth - strwidth(ptext1), 0) * ' ' + '')
            if   i == 0:     line += (' ' + tag + ' ')
            elif tag == ' ': line += (' ' + ' ' + ' ')
            else:            line += (' ' + '^' + ' ')
            line += (pnum2.rjust(6))
            line += ('|')
            line += (ptext2)
            lines.append(line)
            line = ''
        return lines
    
    # 行内差分についてプレーンテキストでフォーマッティングを行う関数
    @staticmethod
    def formatlinetext(num1, num2, linediff, width):
        """
        
        Example:
        >>> import pprint
        >>> pprint.pprint(Differ.formatlinetext(1, 2,
        ...                                     [('!', 'bbb', 'aaaaa'),
        ...                                      (' ', 'cc', 'cc'),
        ...                                      ('+', None, 'dd'),
        ...                                      ('-', 'ee', None)], 80))
        ['[     ]      |!!!++  ++--',
         '[ <-  ]     2|bbb  cc  ee',
         '[  -> ]     3|aaaaaccdd  ']
        """
        
        assert width >= (7 + 6 + 1) + 2
        textwidth = width - (7 + 6 + 1)
        
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
                if strwidth(text1) < strwidth(text2):
                    buffertag += tag * minwidth + '+' * (strwidth(text2) - strwidth(text1))
                else:
                    buffertag += tag * minwidth + '-' * (strwidth(text1) - strwidth(text2))
                buffertext1 += text1 + ' ' * (maxwidth - strwidth(text1))
                buffertext2 += text2 + ' ' * (maxwidth - strwidth(text2))
        
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
        
        return lines

# 独自の形式で等幅フォントのターミナルで表示するための文字列の差分を返す。
def original_diff(lines1, lines2, linejunk, charjunk,
                  cutoff, fuzzy, cutoffchar, context, width):
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
    >>> diff = original_diff(text1, text2, linejunk=None, charjunk=None,
    ...                      cutoff=0.1, fuzzy=0,
    ...                      cutoffchar=False, context=5,
    ...                      width=100)
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
    
    # 差分を抽出
    differ = Differ(linejunk=linejunk,
                    charjunk=charjunk,
                    cutoff=cutoff,
                    cutoffchar=cutoffchar,
                    fuzzy=fuzzy,
                    context=context)
    
    textlinediffs = []
    for diff in differ.compare(lines1, lines2):
        if diff == None:
            yield ''
            for textlinediff in textlinediffs:
                for textline in textlinediff:
                    yield textline
                yield ''
            textlinediffs = []
            continue
        
        ((tag, num1, text1, num2, text2), linediff) = diff
        
        for line in differ.formattext(tag, num1, text1, num2, text2, width):
            yield line
        if tag == '|':
            textlinediffs.append(differ.formatlinetext(num1, num2,
                                                       linediff, width))

def main():
    """main function"""
    
    # オプション解析
    parser = optparse.OptionParser('usage: %prog'
                                   ' [ -f | -c ]'
                                   ' [ -w WIDTH ]'
                                   ' [ other options ]'
                                   ' file1 file2', version='%prog ' + __version__)
    # -fオプション: 差分を抽出した箇所以外のテキスト全体を表示する
    parser.add_option('-f', '--full', action='store_true', default=False,
                      help='Fulltext diff (default False) (disable context option)')
    # -cオプション: 差分を抽出した箇所の前後の行数を指定する（デフォルトは前後5行）
    parser.add_option('-c', '--context', metavar='NUM', type='int', default=5,
                      help='Set number of context lines (default 5)')
    
    # -wオプション: 差分表示時の最大の横幅を指定する（制限する）
    def check_width(option, opt_str, value, parser):
        if value <= 0:
            raise optparse.OptionValueError(\
                '%s option invalid. set a larger number.' % opt_str)
        setattr(parser.values, option.dest, value)
    parser.add_option('-w', '--width', type='int', default=130,
                      action='callback', callback=check_width,
                      help='Set number of width  (default 130)')
    # -rオプション: ディレクトリ比較時にサブディレクトリが見つかった場合、再帰的に比較する
    parser.add_option('-r', '--recursive', action='store_true', default=False,
                      help='Recursively compare any subdirectories found.')
    def check_ratio(option, opt_str, value, parser):
        if not 0.0 <= value <= 1.0:
            raise optparse.OptionValueError(opt_str + ' option invalid.'
                                            ' set number in range'
                                            '(0.0 <= number <= 1.0 ).')
        setattr(parser.values, option.dest, value)
    # 
    def check_regexp(option, opt_str, value, parser):
        try: re.compile(value)
        except:
            raise optparse.OptionValueError(opt_str + ' option invalid. wrong regexp')
        setattr(parser.values, option.dest, value)
    parser.add_option('', '--linejunk', type='string',
                      action='callback', callback=check_regexp,
                      help='linejunk')
    # 
    parser.add_option('', '--charjunk', type='string', action='store',
                      help='charjunk')
    # --cutoffオプション: 差分抽出時の行マージ判定割合を指定する（デフォルトは75%）
    parser.add_option('', '--cutoff', metavar='RATIO', type='float', default=0.75,
                      action='callback', callback=check_ratio,
                      help='Set number of cutoff ratio (default 0.75) (0.0<=ratio<=1.0)')
    # --fuzzyオプション: 差分抽出時のマージ適用調節割合を指定する（デフォルトは0.0%）
    parser.add_option('', '--fuzzy', type='float', metavar='RATIO', default=0.0,
                      action='callback', callback=check_ratio,
                      help='Set number of fuzzy matching ratio (default 0.0) (0.0<=ratio<=1.0)')
    # --cutoffcharオプション: 差分抽出時に文字の変更を分けて表示するかどうかを指定する
    # （デフォルトはFlase(分けない)）
    parser.add_option('', '--cutoffchar', action='store_true', default=False,
                      help='Cutoff character in line diffs (default False)')
    
    def check_codec(option, opt_str, value, parser):
        try: value = codecs.lookup(value).name
        except(LookupError):
            raise optparse.OptionValueError(
                'LookupError: unknown encoding \'' + value + '\'')
        setattr(parser.values, option.dest, value)
    # --enc-file1オプション: 左側のファイルを開く際のコーデックを指定する（デフォルトはutf-8）
    parser.add_option('', '--enc-file1', metavar='ENCODING', type='string', default='utf-8',
                      action='callback', callback=check_codec,
                      help='Set encoding of leftside inputfile1 (default utf-8)')
    # --enc-file2オプション: 右側のファイルを開く際のコーデックを指定する（デフォルトはutf-8）
    parser.add_option('', '--enc-file2', metavar='ENCODING', type='string', default='utf-8',
                      action='callback', callback=check_codec,
                      help='Set encoding of rightside inputfile2 (default utf-8)')
    # --enc-stdoutオプション: 差分を標準出力する際のコーデックを指定する（デフォルトはutf-8）
    parser.add_option('', '--enc-stdout', metavar='ENCODING', type='string', default='utf-8',
                      action='callback', callback=check_codec,
                      help='Set encoding of standard output (default utf-8)')
    # --ignore-crlfオプション: 改行コードの違い（crとlf）を無視する
    parser.add_option('', '--ignore-crlf', action='store_true', default=False,
                      help='Ignore carriage return (\'\\r\') and line feed (\'\\n\') (default False)')
    # -uオプション: 何もしない。
    # Subversionから呼び出されてときにエラーとならないための互換性のためにある。
    parser.add_option('-u', action='store_true', help='Do nothing'
    ' (It is accepted only for compatibility with "svn diff --diff-cmd" interface)')
    
    # -Lオプション: 差分表示前にラベルを表示する（最大2回指定可能）
    # Subversionから呼び出された場合を想定したオプション。
    label = []
    def set_label(option, opt_str, value, parser):
        if len(label) >= 2:
            # -Lオプションは3回以上指定してはいけない
            raise optparse.OptionValueError(\
                "%s option invalid. set less than 3 times." % opt_str)
        label.append(value)
    parser.add_option("-L", type="string",
                      action="callback", callback=set_label,
                      help='label of file1 and file2(can set 2 times)')
    
    def _test(option, opt_str, value, parser):
        doctest.testmod(verbose=True)
        parser.exit()
    # --testオプション: テストコードを実行
    parser.add_option('', '--test', action='callback', callback=_test, help='Test self')
    
    # オプション解析を実行
    (options, args) = parser.parse_args()
    # 必須引数の個数が所定と異なる場合は
    if len(args) != 2:
        # メッセージを表示して終了
        parser.error('Need to specify both a file1 and file2')
    
    # 引数を変数に設定
    file_or_dir1, file_or_dir2 = args
    context = options.context
    full = not options.full
    
    if options.full:
        context = None
    else:
        context = options.context
    
    if options.linejunk != None:
        linejunk = lambda line: re.compile(options.linejunk).match(line) is not None
    else:
        linejunk = None
    
    if options.charjunk != None:
        charjunk = lambda char: char in options.charjunk
    else:
        charjunk = None

    cmpdir = None
    cmplist = []
    if   os.path.isdir(file_or_dir1) and os.path.isdir(file_or_dir2):
        # diff [DIR] and [DIR]
        cmpdir = dircmp(file_or_dir1, file_or_dir2)
        cmplist = cmpdir.tree(recursive=options.recursive)
        print('')
    elif os.path.isdir(file_or_dir1):
        # diff [DIR/FILE] and [FILE]
        cmplist = [(os.path.join(file_or_dir1, os.path.basename(file_or_dir2)), file_or_dir2)]
    elif os.path.isdir(file_or_dir2):
        # diff [FILE] and [DIR/FILE]
        cmplist = [(file_or_dir1, os.path.join(file_or_dir2, os.path.basename(file_or_dir1)))]
    else:
        # diff [FILE] and [FILE]
        cmplist = [(file_or_dir1, file_or_dir2)]
    
    for file1, file2 in cmplist:
        # 標準出力用の文字コードを明示的に指定する
        # cygwinではなぜか正常に自動判定されなかった・・・
        
        # for Python3.1
        # sys.stdout = open(sys.stdout.fileno(), 'w', encoding=options.enc_stdout)
        # for Python2.6 and Jython2.5
        # sys.stdout = codecs.lookup(options.enc_stdout)[-1](sys.stdout)
        
        # 入力ファイルを開く
        lines1 = None
        lines2 = None
        try:
            # for Python3.1
            # lines1 = open(file1, 'r', encoding=options.enc_file1).readlines()
            # lines2 = open(file2, 'r', encoding=options.enc_file2).readlines()
            # for Python2.6 and Python2.5 and Jython2.5
            lines1 = codecs.open(file1, 'r', encoding=options.enc_file1).readlines()
            lines2 = codecs.open(file2, 'r', encoding=options.enc_file2).readlines()
        # for Python2.6 and Python2.5 and Jython2.5
        except IOError:
            if lines1 == None:
                filename = file1
            else:
                filename = file2
            print('[Errno 2] No such file or directory: \'' + filename + '\'')
            return 1
        except UnicodeDecodeError:
            if lines1 == None:
                filename = file1
                encoding_text = options.enc_file1
                optionname = '--enc-file1'
            else:
                filename = file2
                encoding_text = options.enc_file2
                optionname = '--enc-file2'
            print('\'' + filename  + '\' is not encoding by \'' + encoding_text + '\'')
            print('Set correct encoding of \'' + filename + '\' by ' + optionname + ' option')
            return 1
        # for Python3.1 and Python2.6
        # except IOError as error:
        #     print(str(error))
        # except UnicodeDecodeError as error:
        #     print(str(error))
        
        # ラベルが-Lオプションで明示的に指定されていなければ、
        # ファイル名をラベルとして使用する
        if len(label) == 0: label.append(file1)
        if len(label) == 1: label.append(file2)
        if cmpdir != None:
            label[0] = file1
            label[1] = file2
        
        if options.ignore_crlf:
            lines1 = [line.rstrip('\r\n') for line in lines1]
            lines2 = [line.rstrip('\r\n') for line in lines2]
        
        # expandtabsは幅広文字に対応していないので自前で対処する
        # 以下のコードを試せば分かる
        # unicodestr = u'aあ\tb'
        # print(unicodestr.expandtabs(8).encode('sjis'))
        # print(unicodestr.encode('sjis'))
        
        print('--- ' + label[0] + ' (' + options.enc_file1 + ')')
        print('+++ ' + label[1] + ' (' + options.enc_file2 + ')')
        
        diff = original_diff(lines1, lines2, linejunk=linejunk,
                             charjunk=charjunk,
                             cutoff=options.cutoff,
                             fuzzy=options.fuzzy,
                             cutoffchar=options.cutoffchar,
                             context=context,
                             width=options.width)
        for line in diff: print(line.encode(options.enc_stdout))
        
    return 0

if __name__ == "__main__":
    main()
    # doctest.testmod()
    # profile.run('main()')
    # pdb.runcall(main)


