def armored(value):
    if not value.will_collapse():
        return '({0})'.format(value)
    else:
        return value


def print_prepared(value):
    if isinstance(v1alue, int):
        value = hex(value)
    else:
        value = armored(value)
    return value


class Value:
    def __and__(self, other):
        return BitwiseAndResult(self, other)

    def __or__(self, other):
        return BitwiseOrResult(self, other)

    def will_collapse(self):
        raise NotImplementedError


class UnknownValue(Value):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def will_collapse(self):
        return True


class MemoryRead(Value):
    def __init__(self, base, offset, size):
        self.base = base
        self.offset = offset
        self.size = size

    def will_collapse(self):
        return True

    def __str__(self):
        return '({2})D[{0}+{1}]'.format(self.base, self.offset, 'b' + str(self.size * 8))


class BitwiseAndResult(Value):
    def __init__(self, value1, value2):
        self.v1, self.v2 = value1, value2

    def will_collapse(self):
        return isinstance(self.v1, int) and isinstance(self.v2, int)
    
    def __str__(self):
        v1 = self.v1
        v2 = self.v2
        if isinstance(v1, int) and isinstance(v2, int):
            return str(v1 & v2)
        else:


            if isinstance(v2, int):
                v2 = hex(v2)
            else:
                v2 = armored(v2)

            return '{0} & {1}'.format(v1, v2)


class BitwiseOrResult(Value):
    def __init__(self, value1, value2):
        self.v1, self.v2 = value1, value2

    def will_collapse(self):
        return isinstance(self.v1, int) and isinstance(self.v2, int)
    
    def __str__(self):
        v1 = self.v1
        v2 = self.v2
        if isinstance(v1, int) and isinstance(v2, int):
            return str(v1 | v2)
        else:
            v1 = print_prepared(v1)
            v2 = print_prepared(v2)

            return '{0} | {1}'.format(v1, v2)