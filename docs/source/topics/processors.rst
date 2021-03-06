
.. _preprocessors and postprocessors:

Preprocessors and Postprocessors
================================

Sometimes, you want to run a certain piece of code before/after every
request to a resource.  For example, maybe the resource is only accessible
to authenticated users. This can be done easily with preprocessors and postprocessors.
The preprocessors and postprocessors lists are the functions that are called before
and after the ``apimethod`` decorated function runs.  They are run in the order in which
they are described in the list.

.. testcode:: processors, picky_processors

    from ripozo import ResourceBase, apimethod, RequestContainer

    def pre1(cls, function_name, request):
        print('In pre1')

    def pre2(cls, function_name, request):
        print('In pre2')

    def post1(cls, function_name, request, resource):
        print('In post1')

    class MyResource(ResourceBase):
        preprocessors = [pre1, pre2]
        postprocessors = [post1]

        @apimethod(methods=['GET'])
        def say_hello(cls, request):
            print('hello')
            return cls(properties=dict(hello='world'))

.. doctest:: processors

    >>> res = MyResource.say_hello(RequestContainer())
    In pre1
    In pre2
    hello
    In post1

These can be used to perform any sort of common functionality across
all requests to this resource.  Preprocessors always get the class as
the first argument and the request as the second.  Postprocessors get an
additional resource argument as the third.  The resource object is the return
value of the apimethod.


The picky_processor
"""""""""""""""""""

Sometimes you only want to run pre/postprocessors
for specific methods.  In those cases you can use
the picky_processor.  The picky_processor allows you
to pick which methods you or don't want to run the
pre/postprocessors

.. testcode:: picky_processors

    from ripozo import picky_processor

    class PickyResource(ResourceBase):
        # only runs for the specified methods
        preprocessors = [picky_processor(pre1, include=['say_hello']),
                         picky_processor(pre2, exclude=['say_hello'])]

        @apimethod(methods=['GET'])
        def say_hello(cls, request):
            print('hello')
            return cls(properties=dict(hello='world'))

        @apimethod(route='goodbye', methods=['GET'])
        def say_goodbye(cls, request):
            print('goodbye')
            return cls(properties=dict(goodbye='world'))

The picky_processor allows you to pick which
methods to run the preprocessor by looking at the name
of the processor.  If it's not in the exclude list or
in the include list it will be run.  Otherwise
the preprocessor will be skipped for that method.


.. doctest:: picky_processors

    >>> res = PickyResource.say_hello(RequestContainer())
    In pre1
    hello
    >>> res = PickyResource.say_goodbye(RequestContainer())
    In pre2
    goodbye

Picky Processor
^^^^^^^^^^^^^^^

.. autofunction:: ripozo.utilities.picky_processor
