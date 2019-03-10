class Scope(object):
    def __init__(self, parent, item = None):
        self.parent = None
        self.item = None

        self._indentation = 0
        self.position = 0
        self.continuation = False

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
        while scope.parent is not None:
            scope = scope.parent
            length += 1
        return length

    def __getitem__(self, index):
        scope = self

        if index < 0:
            for i in range(-index):
                item = scope.item
                scope = scope.parent
        else:
            raise IndexError('Not implemented')

        return item

    def __setitem__(self, index, item):
        scope = self

        if index < 0:
            for i in range(-index-1):
                scope = scope.parent
        else:
            raise IndexError('Not implemented')
        scope.item = item

    def __iter__(self):
        scope = self
        while scope.parent is not None:
            item = scope.item
            scope = scope.parent
            yield item

    def __eq__(self, other):
        if not isinstance(other, Scope):
            return False
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
            while scope.parent is not None:
                if item in scope.item:
                    if helper(scope.parent):
                        return True

                    if scope.parent.parent is not None:
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
            if s in ['{', 'flow', 'initializer list']:
                scopes += 1
        return scopes + self.indentation

    def is_global(self):
        for s in self:
            if s in ['{', 'initializer list']:
                return False
        return True

    def get_last(self):
        if not self.item:
            return ''

        return self.item

    def set_last(self, item):
        self.item = item

    last = property(get_last, set_last)

    def get_indentation(self):
        return self._indentation + self.continuation

    def set_indentation(self, indentation):
        self._indentation = indentation

    indentation = property(get_indentation, set_indentation)
