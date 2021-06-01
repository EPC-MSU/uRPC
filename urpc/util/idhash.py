class IdentityHash:
    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return id(self)
