# reformat.py

What I wanted was being able to press a single hotkey in emacs while writing
either C++, Python or MATLAB, and then suddenly have the whole file formatted
in a way that I prefer. There are many beautifiers/formatters out there,
but most of them only work for C++ style languages, don't do exactly what
I want, and contain 20k+ lines of code.

Here I intend to create such a tool in a small amount of code. Reason I
believe this is possible is because I already have a version that is nearly
working for all of my C++ code with only 200 lines of code, and because
I'm using Python, which already has many features built-in that make
for easy parser writing.

The current state is that in terms of formatting, not indenting, it can
almost generate the same result as when using for instance astyle.

Next thing I want to do is making my parser aware of scopes, so that I can
fix my pointer/reference padding and implement indentation generation.
After this I will try to make it work for both Python and MATLAB.
