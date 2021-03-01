"""
This file is licensed under the same terms as Python itself.

Copyright Oz N Tiram <oz.tiram@gmail.com> 2016.

Note: This should be a Python module.

Make class properties readonly.
Why not use @property?

Because it's verbose, and you need to create a function which returns
something.

.. code:

   class MyClass:

		@property
		def a(self):
			return 1


Now if you decide to refactor this you got some work to do.
The same goes if you have a class with many attributes that you want to
refactor to properties:

.. code:

	class AClassWithManyAttributes:

		 def __init__(a, b, c, d, e ...)
			 self.a = a
			 self.b = b
			 self.c = c
			 ....

Now refactoring this would be very verbose (an IDE will save you a lot of
typing, but it won't make the code shorter:

   .. code::

   class AClassWithManyAttributes:
		'''refactored to properties'''
		def __init__(a, b, c, d, e ...)
			 self._a = a
			 self._b = b
			 self._c = c
		@property
		def a(self):
			return self._a
		@property
		def b(self):
			return self._b
		@property
		def b(self):
			return self._c
		# you get this ... it's long


Now imagine you can simply do that:

.. code:

	@read_only('a', 'b', 'c')
	class AClassWithManyAttributes:

		 def __init__(a, b, c, d, e ...)
			 self.a = a
			 self.b = b
			 self.c = c

This makes the attributes read only, trying to assign will raise
and exception.

Well, stop imagining, here is the code...
"""

def read_only_properties(*attrs):

	def class_rebuilder(cls):
		"The class decorator example"

		class NewClass(cls):
			"This is the overwritten class"
			def __setattr__(self, name, value):

				if name not in attrs:
					pass
				elif name not in self.__dict__:
					pass
				else:
					raise AttributeError("Can't touch {}".format(name))

				super().__setattr__(name, value)

		return NewClass

	return class_rebuilder

# example usage
"""
@read_only_properties('readonly', 'forbidden')
class MyClass(object):
	def __init__(self, a, b, c):
		self.readonly = a
		self.forbidden = b

m = MyClass(1, 2, 3)
m.ok = 3
print(m.ok, m.readonly)

# can touch ok
print("This worked...")
# this will explode
m.forbidden = 4
"""
