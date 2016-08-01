class Scope(object):
    def __init__(self, parent, item = None):
        self.parent = None
        self.item = None
        if not item:
            if isinstance(parent, int):
                if parent > 0:
                    self.parent = Scope(parent - 1)
                    self.item = '{'
            elif isinstance(parent, Scope):
                self.parent = parent.parent
                self.item = parent.item
        else:
            self.parent = parent
            self.item = item

    def __len__(self):
        scope = self
        length = 0
        while scope.parent:
            scope = scope.parent
            length += 1
        return length

    def __nonzero__(self):
        return True

    def __getitem__(self, index):
        scope = self

        if index < 0:
            for i in xrange(-index):
                item = scope.item
                scope = scope.parent
        else:
            raise IndexError('Not implemented')

        return item

    def __setitem__(self, index, item):
        scope = self

        if index < 0:
            for i in xrange(-index-1):
                scope = scope.parent
        else:
            raise IndexError('Not implemented')
        scope.item = item

    def __iter__(self):
        scope = self
        while scope.parent:
            item = scope.item
            scope = scope.parent
            yield item

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return repr([self.parent, self.item])

    def __contains__(self, item):
        for i in self:
            if item in i:
                return True
        return False

    def remove(self, item):
        def helper(scope):
            '''Recursively iterates over nested lists to find the
            deepest match. Returns after if nothing was found'''
            while scope.parent:
                if scope.parent and item in scope.item:
                    if helper(scope.parent):
                        return True

                    if scope.parent.parent:
                        scope.item = scope.parent.item
                        scope.parent = scope.parent.parent
                    else:
                        scope.item = None
                        scope.parent = None
                    return True
                scope = scope.parent
            return False

        scope = self
        error = ValueError('Item \'%s\' not found in scope \'%s\'' % (item, self))
        if not len(scope):
            raise error

        if not helper(scope):
            raise error

    def indented_scopes(self):
        scopes = 0
        for s in self:
            if s in ['{', 'continuation']:
                scopes += 1
        return scopes

    def is_global(self):
        for s in self:
            if s in ['{', 'initializer list']:
                return False
        return True

    def get_last(self):
        if not self.item:
            return ''

        for s in self:
            if s != 'continuation':
                return s

        return ''

    def set_last(self, item):
        scope = self
        while scope.parent:
            if scope.item != 'continuation':
                scope.item = item
                return
            scope = scope.parent

    last = property(get_last, set_last)
