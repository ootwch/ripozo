from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import six

from ripozo.decorators import apimethod
from ripozo.exceptions import BaseRestEndpointAlreadyExists
from ripozo.viewsets.constructor import ResourceMetaClass
from ripozo.viewsets.resource_base import ResourceBase
from ripozo_tests.helpers.inmemory_manager import InMemoryManager
from ripozo_tests.python2base import TestBase

import unittest


logger = logging.getLogger(__name__)


class MM1(InMemoryManager):
    model = 'Something'
    _model_name = 'modelname'

name_space = '/mynamspace/'


class TestResource(ResourceBase):
    __abstract__ = True
    _manager = MM1
    _resource_name = 'myresource'
    _namespace = name_space


class TestResourceBase(TestBase, unittest.TestCase):
    def setUp(self):
        ResourceMetaClass.registered_resource_classes.clear()

    def test_abstract_not_implemented(self):
        """
        asserts that a class that inherits from
        resource base with __abstract__ == True
        is not registered on the ResourceMetaClass
        """
        class TestResourceClass(ResourceBase):
            __abstract__ = True
        self.assertEqual(len(ResourceMetaClass.registered_resource_classes), 0)

    def test_resource_name(self):
        """Tests whether the resource_name is properly constructed"""
        resourcename = 'myresource'

        class T1(TestResource):
            __resource_name__ = resourcename
        self.assertEqual(resourcename, T1.resource_name)

    def test_resource_name2(self):
        """
        Tests whether the resource_name is properly retrieved from
        manager if the resource_name is not specified.
        """
        class T2(TestResource):
            _resource_name = None

            __manager__ = MM1
        self.assertEqual(T2.resource_name, 't2')

    def test_manager_property(self):
        """Tests whether the manager instance is properly instantiated"""
        class T1(TestResource):
            __manager__ = MM1
        self.assertIsInstance(T1.manager, MM1)

    def test_base_url(self):
        """Tests whether the base_url is properly constructed"""
        class T1(TestResource):
            pks = ['something', 'another_thing']
        self.assertIsInstance(T1.base_url, six.text_type)
        self.assertIn(name_space, T1.base_url)
        self.assertIn(T1.resource_name, T1.base_url)
        for pk in T1.pks:
            self.assertIn(pk, T1.base_url)

    def test_minimal_base_url(self):
        """Tests the url when no resource name or namespace is specified"""
        class SomeResource(ResourceBase):
            pass

        self.assertEqual('/some_resource', SomeResource.base_url)

        class AnotherResource(ResourceBase):
            _resource_name = 'another_resource'

        self.assertEqual('/another_resource', AnotherResource.base_url)

        class FinalResource(ResourceBase):
            _namespace = '/api'

        self.assertEqual('/api/final_resource', FinalResource.base_url)

    def test_messed_up_slashes_on_base_url(self):
        """Tests whether the ResourceBase always appropriately replaces
        forward slashes on urls"""
        class DoubleSlash(ResourceBase):
            _namespace = '/'
            _resource_name = '/'

        self.assertEqual('/', DoubleSlash.base_url)
        ResourceMetaClass.registered_resource_classes.clear()

        class DoublSlash2(ResourceBase):
            _namespace = '//'
            _resource_name = '/double_slash'

        self.assertEqual('/double_slash', DoublSlash2.base_url)
        ResourceMetaClass.registered_resource_classes.clear()

        class DoubleMiddleSlash(ResourceBase):
            _namespace = 'api/'
            _resource_name = '//another_resource/'

        self.assertEqual('/api/another_resource/', DoubleMiddleSlash.base_url)

    def test_class_registered(self):
        """Tests whether an implement Resource is registered on the meta class"""
        class T1(TestResource):
            pass
        self.assertIn(T1, six.iterkeys(ResourceMetaClass.registered_resource_classes))

    def test_register_endpoint(self):
        """Tests whether the endpoint is registered on the class"""
        class T1(TestResource):
            @apimethod(methods=['GET'])
            def my_api_method1(self):
                pass
        # for python 3.3  Otherwise it never gets registered for some reason
        print(T1.__name__)

        self.assertIn('my_api_method1', T1.endpoint_dictionary())

    def test_base_url_duplication_exception(self):
        """Tests whether an excption is raised if the base_url
        already exists"""
        class T1(TestResource):
            pass

        try:
            class T2(TestResource):
                pass
            assert False
        except BaseRestEndpointAlreadyExists:
            pass

    def test_init(self):
        """Just tests whether the __init__ method initializes without exception"""
        class T1(TestResource):
            pass
        # TODO add more once you determine exactly what the __init__ should do
        x = T1()

    def test_url_property(self):
        """Tests whether the url for an individual resource is properly created"""
        class T1(TestResource):
            namespace = '/api'
            pks = ['pk']
            _resource_name = 'my_resource'

        x = T1(properties={'pk': 1})
        self.assertEqual(x.url, '/api/my_resource/1')

    def test_multiple_resources_endpoint_dictionaries(self):
        """
        Ran into a bug where the _endpoint_dictionary was getting
        overridden and therefore all resources returned the same
        endpoints
        """

        class T1(ResourceBase):
            @apimethod(methods=['GET'])
            def hello(cls, *args, **kwargs):
                return cls(properties=dict(hello='world'))

        endpoint = T1.endpoint_dictionary()['hello'][0]
        self.assertEqual(endpoint['route'], '/t1/')
        self.assertListEqual(endpoint['methods'], ['GET'])

        # The routes in this should be different
        class T2(T1):
            pass

        # Ensure the T1 endpoint dictionary is the same as before
        endpoint = T1.endpoint_dictionary()['hello'][0]
        self.assertEqual(endpoint['route'], '/t1/')
        self.assertListEqual(endpoint['methods'], ['GET'])

        # Make sure the T2 endpoint dictionary has a different route
        endpoint = T2.endpoint_dictionary()['hello'][0]
        self.assertEqual(endpoint['route'], '/t2/')
        self.assertListEqual(endpoint['methods'], ['GET'])
