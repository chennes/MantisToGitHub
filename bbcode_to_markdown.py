# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2021 Chris Hennes <chennes@pioneerlibrarysystem.org>    *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENSE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import re
import sys

class BBCodeToMarkdown:
    """ Convert text containing BBCode characters to GitHub-flavored markdown. Only Markdown is emitted,
    no HTML tags are used. Unsupported BBCode tags are silently removed. Nesting is partially supported.
    This is a naive converter based on regular expressions, it does NOT do any real language parsing. """

# BBCode tags and their treatment:
# [b]Text[/b] -> Bold, maps to **Text**
# [i]Text[/i] -> Italic, maps to *Text*
# [s]Text[/s] -> Strikethrough, maps to ~~Text~~
# [u][/u] -> Underline, not supported, stripped
# [color=yellow][/color] -> Colored text, not supported, stripped
# [highlight=blue][/highlight] -> Colored background, not supported, stripped
# [size=125][/size] -> Size is not directly supported, but 125 is made an H1 if it's on its own line
# [sup][/sup] -> Not supported, stripped
# [sub][/sub] -> Not supported, stripped
# [list][*][/list] -> Converted to a Markdown-style list, either bulleted or numbered as needed
# [code=lang][/code] -> Code: if on its own line(s), ```code``` is used. If inline, `code`.
# [quote=bob][/quote] -> Replaced by a blockquote: > 
# [hr] -> Replaced by === and the required blank lines
# [left][/left] -> Not supported, stripped
# [center][/center] -> Not supported, stripped
# [right][/right] -> Not supported, stripped
# [justify][/justify] -> Not supported, stripped
# [url=link]text[/url] -> Link, replaced with [text](link)
# [email=chennes@]Your email here[/email] -> Replaced with a mailto: link as above
# [img]link[/img] -> Image, replaced with !(link)

    def __init__ (self, bbcode:str):
        self.text = bbcode

    def md (self) -> str:
        self.strip_unsupported()
        self.bold()
        self.italic()
        self.size()
        self.list()
        self.code()
        self.quote()
        self.hr()
        self.url()
        self.email()
        self.img()
        return self.text

    def strip_unsupported(self):
        unsupported_tags = ["u", "color", "highlight", "sup", "sub", "left", "center", "right", "justify"]
        for tag in unsupported_tags:
            search_regex = f"\\[{tag}.*?\\](.*?)\\[/{tag}\\]"
            self.text = re.sub(search_regex, "\\1", self.text, flags=re.IGNORECASE)

    def bold(self):
        search_regex = r"\[b\](.*?)\[/b\]"
        self.text = re.sub(search_regex, "***\\1***", self.text, flags=re.IGNORECASE)

    def italic(self):
        search_regex = r"\[i\](.*?)\[/i\]"
        self.text = re.sub(search_regex, "**\\1**", self.text, flags=re.IGNORECASE)

    def size(self):
        search_regex = "\n\\[size\s*=\s*125\\](.*?)\\[/size\\]\n"
        self.text = re.sub(search_regex, "\n# \\1\n", self.text, flags=re.IGNORECASE)
        search_regex = f"\\[size.*?\\](.*?)\\[/size\\]"
        self.text = re.sub(search_regex, "\\1", self.text, flags=re.IGNORECASE)

    def list(self):
        # Does NOT support nested (multi-level) lists, or list items that have newline characters in them

        # Ordered lists that start at some number n
        search_regex = "\\[list\\s*=\\s*([0-9]+)\\](.*?)\\[/list\\]"
        list_item_regex = "\\s*\\[\\*\\](.*)"
        list_item_matcher = re.compile(list_item_regex)
        outer_pattern= re.compile(search_regex, flags=re.IGNORECASE|re.DOTALL)
        match = outer_pattern.search(self.text)
        while match is not None:
            list_item_number = int(match.group(1))
            list_contents = match.group(2)
            span = match.span()
            parsed_list_text = ""
            list_item_iterator = list_item_matcher.finditer(list_contents)
            for list_item in list_item_iterator:
                parsed_list_text += f"{list_item_number}. {list_item.group(1)}\n"
                list_item_number += 1
                list_item = list_item_matcher.search(list_contents)
            new_string = self.text[0:span[0]] + parsed_list_text + self.text[span[1]:]
            self.text = new_string
            match = outer_pattern.search(self.text)

        # Unordered lists are slightly simpler:
        search_regex = "\\[list.*?\\](.*?)\\[/list\\]"
        list_item_matcher = re.compile(list_item_regex)
        outer_pattern= re.compile(search_regex, flags=re.IGNORECASE|re.DOTALL)
        match = outer_pattern.search(self.text)
        while match is not None:
            list_contents = match.group(1)
            span = match.span()
            list_contents = list_contents.replace("[*]","* ")
            new_string = self.text[0:span[0]] + list_contents + self.text[span[1]:]
            self.text = new_string
            match = outer_pattern.search(self.text)

    def code(self):
        # Inline code:
        search_regex = "\\[code.*?\\](.*?)\\[/code\\]"
        self.text = re.sub(search_regex, "`\\1`", self.text, flags=re.IGNORECASE)
        # Block of code:
        search_regex = "\\[code.*?\\](.*?)\\[/code\\]\n"
        self.text = re.sub(search_regex, "```\\1```\n", self.text, flags=re.IGNORECASE|re.DOTALL)

    def quote(self):
        search_regex = "\\[quote.*?\\]\n(.*?)\n\\[/quote\\]\n"
        quote_matcher = re.compile(search_regex, flags=re.IGNORECASE|re.DOTALL)
        match = quote_matcher.search(self.text)
        while match is not None:
            span = match.span()
            quote_contents = match.group(1)
            lines = quote_contents.split("\n")
            quote_in_markdown = ""
            for line in lines:
                quote_in_markdown += "> " + line + "\n"
            new_string = self.text[0:span[0]] + quote_in_markdown + self.text[span[1]:]
            self.text = new_string
            match = quote_matcher.search(self.text)


    def hr(self):
        pass

    def url(self):
        pass

    def email(self):
        pass

    def img(self):
        pass 

def selftest():
    text = """
Some text. [b]Some bold text[/b]. [i]Some italic text[/i].

These tags should all get stripped:
[u]Some underlined text (no matching markdown)[/u].
[color=blue]This text used to be blue. It's not now.[/color]
[highlight=yellow]This was highlighted in the BBCode, but not in the Markdown.[/highlight]
[sup]This was superscript, but is not now.[/sup]
[sub]This was subscript, but is not now.[/sub]
[left]This was left-aligned, but is not now.[/left]
[center]This was centered, but is not now.[/center]
[right]This was right-aligned, but is not now.[/right]
[justify]This was justified, but is not now.[/justify]

Size is special:
[size=125]This is a heading[/size]
[size=100]This is just plain text, the size has been stripped.[/size]
[size=125]This is also plain text[/size], because it's not on its own line.

Lists:
[list]
[*] This is a bullet point in an unordered list
[*] This is a second bullet point in an unordered list
[/list]
[list=2]
[*] This is a bullet point in an ordered list, starting from item 2
[*] This is a second bullet point in an ordered list, but numbered 3
[/list]

Code:
This is a chunk of text containing [code]A little bit of code[/code].
[code]
This is some real code, in a block
[/code]
[code=top_sekrit_language]
Markdown does not care what language the code is in
[/code]

Quotes:
[quote="some guy"]
Markdown does not care who the quote is by, or when it happened
[/quote]
    """

    b = BBCodeToMarkdown(text)
    print (b.md())

if __name__ == '__main__':
    text = sys.argv[1]
    if text == "selftest":
        selftest()
    else:
        b = BBCodeToMarkdown(text)
        print (b.md())