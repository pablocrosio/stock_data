class MyMeta(type):
    def __call__(cls, *args, **kwargs):
        print('MyMeta __call__ called')
        print(f'cls = {cls}')
        #return super(MyMeta, cls).__call__(*args, **kwargs)
        r = super(MyMeta, cls).__call__(*args, **kwargs)
        print(f'type of r = {type(r)}')
        return r

class MyClass(metaclass=MyMeta):
    pass

m = MyClass()
m2 = MyClass()

print(type(m))
print(type(m2))
