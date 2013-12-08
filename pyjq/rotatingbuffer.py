class RotatingBuffer(object):
    def __init__(self):
        self.length = 0
        self.index = 0
        self.data = []

    def push(self, x):
        if self.length == len(self.data):
            if self.index:
                self.data = self.data[self.index:] + self.data[:self.index]
                self.index = 0
            self.data.append(x)
        else:
            i = (self.index + self.length) % len(self.data)
            self.data[i] = x
        self.length += 1

    def __iter__(self):
        return self

    def next(self):
        if not self.length:
            raise StopIteration()
        x = self.data[self.index]
        self.index = (self.index + 1) % len(self.data)
        self.length -= 1
        return x
