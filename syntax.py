# Python syntax highlighter adapted from https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter


def textformat(color, style=''):
    _color = QColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {'keyword': textformat('#4082ed'),
          'operator': textformat('white'),
          'brace': textformat('#c0def9'),
          'defclass': textformat('#f7faff', 'bold'),
          'string': textformat('#468c4b'),
          'string2': textformat('#3eb748'),
          'comment': textformat('#7a7a7a', 'italic'),
          'builtin_var': textformat('#d62a2a', 'bolditalic'),
          'numbers': textformat('#2aafed')}


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    keywords = ['and', 'assert', 'break', 'class', 'continue', 'def',
                'del', 'elif', 'else', 'except', 'exec', 'finally',
                'for', 'from', 'global', 'if', 'import', 'in',
                'is', 'lambda', 'not', 'or', 'pass', 'print',
                'raise', 'return', 'try', 'while', 'yield',
                'None', 'True', 'False']

    operators = ['=', '==', '!=', '<', '<=', '>', '>=',
                 '\+', '-', '\*', '/', '//', '\%', '\*\*',
                 '\+=', '-=', '\*=', '/=', '\%=',
                '\^', '\|', '\&', '\~', '>>', '<<']

    braces = ['\{', '\}', '\(', '\)', '\[', '\]']

    def __init__(self, document):

        super().__init__(document)

        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword']) for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator']) for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace']) for b in PythonHighlighter.braces]

        # All other rules
        rules += [(r'\bself\b', 0, STYLES['builtin_var']),
                  (r'\bfig\b', 0, STYLES['builtin_var']),
                  (r'\baxis\b', 0, STYLES['builtin_var']),
                  (r'\bnp\b', 0, STYLES['builtin_var']),
                  (r'\bOut\b', 0, STYLES['builtin_var']),

                  # Double-quoted string, possibly containing escape sequences
                  (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
                  # Single-quoted string, possibly containing escape sequences
                  (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

                  # 'def' followed by an identifier
                  (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
                  # 'class' followed by an identifier
                  (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

                  # From '#' until a newline
                  (r'#[^\n]*', 0, STYLES['comment']),

                  # Numeric literals
                  (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
                  (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        # Do other syntax formatting
        for expression, nth, textformat in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, textformat)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
