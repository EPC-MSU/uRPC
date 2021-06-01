# TODO: implement singleton for immutable FieldType objects
class FieldTypeMeta(type):
    pass


class FieldType(metaclass=FieldTypeMeta):
    pass


# Immutable types descriptions
class IntegerType(FieldType):
    def __init__(self, signed, size):
        self._signed = signed
        self._size = size

    @property
    def signed(self):
        return self._signed

    @property
    def size(self):
        return self._size

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._signed == other._signed and self._size == other._size

    # def __ne__(self, other):
    #     return not self.__eq__(other)

    def __hash__(self):
        return hash((self._signed, self._size))

    def __repr__(self):
        """
         Don't change, using in temlates
        """
        # TODO: make templates not rely on repr method for theirs output generation!
        return "{}int{}".format("" if self.signed else "u", self.size * 8)


class FloatType(FieldType):
    def __init__(self, size):
        self._size = size

    @property
    def size(self):
        return self._size

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._size == other._size

    def __hash__(self):
        return hash(self._size)

    def __repr__(self):
        return "float"


class ArrayType(FieldType):
    def __init__(self, _type, length):
        self._type = _type
        self._length = length

    @property
    def type(self):
        return self._type

    @property
    def signed(self):
        return self.type.signed

    @property
    def size(self):
        return self._length * self.type.size

    def __len__(self):
        return self._length

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.type == other.type and self._length == other._length

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._type, self._length))

    def __repr__(self):
        return "{}[{}]".format(self.type, len(self))


Integer64s = IntegerType(True, 8)
Integer64u = IntegerType(False, 8)
Integer32s = IntegerType(True, 4)
Integer32u = IntegerType(False, 4)
Integer16s = IntegerType(True, 2)
Integer16u = IntegerType(False, 2)
Integer8s = IntegerType(True, 1)
Integer8u = IntegerType(False, 1)
Float = FloatType(4)
Array = ArrayType
