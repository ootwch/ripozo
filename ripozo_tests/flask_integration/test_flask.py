# Only tested for python 3

import unittest
from flask import Flask, json
from flask_ripozo import FlaskDispatcher
from ripozo import restmixins, manager_base, apimethod
from ripozo.resources.resource_base import ResourceBase
from ripozo.resources.relationships import Relationship, ListRelationship, FilteredRelationship
from ripozo import adapters
from pprint import pprint
from ripozo.utilities import  join_url_parts
from ripozo.decorators import classproperty

# Flask configuration
DEBUG = True



class Manager(manager_base.BaseManager):
    @classmethod
    def create(cls, values, *args, **kwargs):
        # ItemSelection
        rval = dict(
            basketid='123',
            basket_relation='123',
            itemid='987',
            value_1='Uno',
            value_2='Due',

        )
        return rval

    @classmethod
    def retrieve_list(cls, filters, *args, **kwargs):
        #Itemselection
        rval = [dict(
            basketid='123',
            basket_relation='123',
            itemid='987',
            value_a='One',
            value_b='Two',
        )]
        return rval

    @classmethod
    def retrieve(self, lookup_keys, *args, **kwargs):
        rval = dict(
            basketid='123',
            basket_relation='123',
            itemid='987',
            value_x='Uno',
            value_y='Due',
        )
        return rval





class FlaskAppTest(unittest.TestCase):
    def setUp(self):

        # create our little application :)
        self.flask_app = Flask(__name__)
        self.url_prefix = '/testing/ripozo/api/v1.0'
        self.host = 'http://localhost'

        self.app = self.flask_app.test_client()
        self.dispatcher = FlaskDispatcher(self.flask_app, url_prefix=self.url_prefix)
        self.dispatcher.register_adapters(adapters.HalAdapter)

    def get_rule_list(self):
        return [each.rule for each in self.app.application.url_map.iter_rules()]
        # url_list = []
        # for rule in self.app.application.url_map.iter_rules():
        #     url_list.append(rule.rule)
        # return url_list

    def test_append_slash(self):
        """
        Verify that the 'append_slash' attribute works as expected.
        :return:
        """
        class WithSlash(restmixins.Retrieve):
            manager = Manager
            resource_name = 'withslash'
            pks = ('withslash_is',)
            append_slash = True
        self.dispatcher.register_resources(WithSlash)

        class NoSlash(restmixins.RetrieveList):
            manager = Manager
            resource_name = 'noslash'
            pks = ('noslash_is',)
            append_slash = False
        self.dispatcher.register_resources(NoSlash)

        rule_list = self.get_rule_list()
        print(rule_list)

        self.assertIn('/testing/ripozo/api/v1.0/withslash/<withslash_is>/', rule_list)
        self.assertIn('/testing/ripozo/api/v1.0/noslash/<noslash_is>', rule_list)

    def test_relation_name_property(self):
        """
        Dict lookup issue - this fails if the name of the relationship also exists as property.
        """
        class MyResource(restmixins.Create):
            manager = Manager
            resource_name = 'myresource'
            pks = ('basketid',)

            _relationships = (
                Relationship('value_1', relation='SomethingElse'),
            )

        class SomethingElse(restmixins.Retrieve):
            manager = Manager
            resource_name = 'somethingelse'
            pks = ('ste_id',)

        self.dispatcher.register_resources(MyResource)
        self.dispatcher.register_resources(SomethingElse)

        rv_post = self.app.post(self.url_prefix+'/myresource', data=json.dumps({}), content_type='application/json')
        self.assertEqual('201 CREATED', rv_post.status)




    def test_relation_missing_pk(self):
        """
        Expected to fail explicitly when pk is not found
        """
        class MyResource(restmixins.Create):
            manager = Manager
            resource_name = 'myresource'
            pks = ('basketid',)

            _relationships = (
                Relationship('get_another_object', relation='SomethingElse', property_map=dict(value_1='value_1_translated')),
            )

        class SomethingElse(restmixins.Retrieve):
            manager = Manager
            resource_name = 'somethingelse'
            pks = ('value_axx',)

        self.dispatcher.register_resources(MyResource)
        self.dispatcher.register_resources(SomethingElse)

        rv_post = self.app.post(self.url_prefix+'/myresource', data=json.dumps({}), content_type='application/json')

        print(rv_post)

        obj = json.loads(rv_post.data)
        print(obj)

        print(obj['_links'])

    def test_relation_missing_relation(self):
        """
        Expected to fail explicitly when related resource is not registered
        :return:
        """

        class ItemSelection(restmixins.Retrieve):
            manager = Manager
            resource_name = 'basket'
            _relationships = (Relationship('testtesttest', relation='MissingObject'),)

        with self.assertRaises(KeyError):
            self.dispatcher.register_resources(ItemSelection)




    def test_relation_same_as_pk(self):
        """
        A key should be usable both for the relation as for the primary key
        """
        class MyResource(restmixins.Create):
            manager = Manager
            resource_name = 'myresource'
            pks = ('basketid',)

            _relationships = (
                Relationship('get_another_object', relation='SomethingElse', property_map=dict(value_1='value_1_translated')),
            )

        class SomethingElse(restmixins.Retrieve):
            manager = Manager
            resource_name = 'somethingelse'
            pks = ('value_axx',)

        self.dispatcher.register_resources(MyResource)
        self.dispatcher.register_resources(SomethingElse)

        rv_post = self.app.post(self.url_prefix+'/myresource', data=json.dumps({}), content_type='application/json')

        print(rv_post)

        obj = json.loads(rv_post.data)
        print(obj)

        print(obj['_links'])



    def test_hypermedia_relation_pk(self):
        class BasketFails(restmixins.Retrieve, restmixins.Create):
            manager = Manager
            resource_name = 'basket'
            pks = ('basketid',)

            _relationships = (
                Relationship('basketid', relation='Item'),
            )
            append_slash = False # Just for testing, so as not to get hit by the other issue

        class BasketWorks(restmixins.Retrieve, restmixins.Create):
            manager = Manager
            resource_name = 'basket'
            pks = ('basketid',)

            _relationships = (
                Relationship('basket_relation', relation='Item', property_map=dict(basket_relation='basketid')),
            )
            append_slash = True # Just for testing, so as not to get hit by the other issue

        class Item(restmixins.Retrieve):
            manager = Manager
            resource_name = 'basket'
            pks = ('basketid', 'itemid',)

        self.dispatcher.register_resources(BasketWorks)
        self.dispatcher.register_resources(Item)

        rule_list = self.get_rule_list()
        print(rule_list)

        # Create a new basket and add/select new item 987
        # Returns the created selection object
        data = json.dumps({"item": '987'})
        rv_post_new_basket = self.app.post(self.url_prefix+'/basket/', data=data, content_type='application/json')

        return_data = rv_post_new_basket.data.decode('utf-8')

        # Parse return data and extract 'basket relation' and 'self' link of the new item
        return_data_object = json.loads(return_data)


        print(return_data_object)





    def test_hypermedia_shopping_basket(self):
        """
        A hypermedia example that simulates a shopping basket with relatingships. The basket is a 'collection'
        while it contains individual items.

        First Verification: The collection has a trailing '/', the items don't.
        Second Assertion: The created links are callable.


        :return:
        """

        class Basket(restmixins.Retrieve, restmixins.Create):
            """
            The shopping basket which will contain the items

            Retrieve: Collection of baskets
            Create: New selection into existing or new basket
            """
            manager = Manager
            resource_name = 'basket'
            pks = ('basketid',)
            append_slash = True

            _relationships = (
                Relationship('basket_relation', relation='ItemSelection', property_map=dict(basketid='basketid', itemid='itemid')),
            )

        class ItemSelection(restmixins.Retrieve):
            """
            The link between an Item object and the shopping basket
            'The item is selected to be in this basket'

            Retrieve: Collection of selection items in basket

            """
            manager = Manager
            resource_name = 'basket'
            pks = ('basketid', 'itemid',)
            # Forced to use property map, otherwise the url is not properly built as the attribute is removed from
            # the list of attributes before the url is built.
            # The following does not work:
            # _relationships = (Relationship('basketid', relation='Basket'),)

            _relationships = (
                Relationship('basket_relation2', relation='Basket', property_map=dict(basket_relation='basketid')),
            )

            append_slash = False  # For clarity - this is the default

        self.dispatcher.register_resources(Basket)
        self.dispatcher.register_resources(ItemSelection)

        rule_list = self.get_rule_list()

        # Verify that the rules are created correctly
        self.assertIn('/testing/ripozo/api/v1.0/basket/', rule_list,
                      'The collection of baskets rule has a trailing slash')

        self.assertIn('/testing/ripozo/api/v1.0/basket/<basketid>/', rule_list,
                      'A specific basket is a collection of items and has a trailing slash')

        self.assertIn('/testing/ripozo/api/v1.0/basket/<basketid>/<itemid>', rule_list,
                      'A specific item does not have a trailing slash')

        # Create a new basket and add/select new item 987
        # Returns the created selection object
        data = json.dumps({"item": '987'})
        rv_post_new_basket = self.app.post(self.url_prefix+'/basket/', data=data, content_type='application/json')

        self.assertEqual('201 CREATED', rv_post_new_basket.status, 'Successfully Created?')

        return_data = rv_post_new_basket.data.decode('utf-8')

        # Parse return data and extract 'basket relation' and 'self' link of the new item
        return_data_object = json.loads(return_data)
        basket_selection_link = return_data_object['_links']['basket_relation']['href']
        basket_self_link = return_data_object['_links']['self']['href']

        # The links must be valid calls
        rv_retrieve_basket = self.app.get(basket_self_link) # Call GET with the returned selection link
        rv_retrieve_basket_object = json.loads(rv_retrieve_basket.data.decode('utf-8'))
        print("", flush=True)
        rv_retrieve_selection = self.app.get(basket_selection_link) # Call GET with the returned selection link
        rv_retrieve_selection_object = json.loads(rv_retrieve_selection.data.decode('utf-8'))

        print("", flush=True)

        self.assertEqual(self.host+self.url_prefix+'/basket/123/', basket_self_link)
        self.assertEqual(self.host+self.url_prefix+'/basket/123/987', basket_selection_link)

        self.assertEqual('200 OK', rv_retrieve_basket.status)

        print("POST return:")
        pprint(json.loads(return_data))




class BasketManager(manager_base.BaseManager):
    """
    Very simple key-value store for testing.
    This is not thread safe!
    """

    key_value_store = dict()
    next_basket_key = 1 # For testing only - not thread safe!
    next_relation_key = 1

    @classmethod
    def create(cls, values, *args, **kwargs):
        basket_key = values.get('basket_key', None)
        object_key = values['object_key']  # raises KEYERROR if not given

        if not basket_key:
            basket_key = cls.next_basket_key
            cls.next_basket_key += 1

        relation_key = cls.next_relation_key
        cls.next_relation_key += 1

        key = "{0}::{1}".format(basket_key, relation_key)

        cls.key_value_store[key] = values['object_key']

        r_val, meta = cls.retrieve_list(dict(basket_key=basket_key, relation_key=relation_key, object_key=object_key))
        # resource_name = cls.resource_name
        return dict(basket_key=basket_key, basket=r_val)
        # return dict(basket_key=basket_key)



    @classmethod
    def retrieve_list(cls, filters, *args, **kwargs):
        """
        Returns a list of relations
        :param filters:
        :param args:
        :param kwargs:
        :return:
        """
        basket_key = filters.get('basket_key')
        relation_key = filters.get('relation_key', None)

        if relation_key:
            match = "{0}::{1}".format(basket_key, relation_key)
        elif basket_key:
            match = "{0}::".format(basket_key)
        else:
            match = ""

        rels = [r for r in cls.key_value_store if r.startswith(match)]

        return_list = []
        for r in rels:
            divisor = r.find("::")
            basket_key = r[0:divisor]
            relation_key = r[divisor+2:]
            value = cls.key_value_store[r]
            return_list.append(dict(basket_key=basket_key, relation_key=relation_key, object_key=value))

        return return_list, None

    @classmethod
    def retrieve(cls, lookup_keys, *args, **kwargs):
        """
        Returns exactly one relation, and not a list
        :param lookup_keys:
        :param args:
        :param kwargs:
        :return:
        """
        rval, meta = cls.retrieve_list(lookup_keys) # returns (list, meta) tuple
        if not rval:
            return None
        return rval[0]






class FlaskBasketTest(unittest.TestCase):
    def setUp(self):

        self.flask_app = Flask(__name__)
        self.url_prefix = '/testing/ripozo/api/v1.0'
        self.host = 'http://localhost'

        self.app = self.flask_app.test_client()
        self.dispatcher = FlaskDispatcher(self.flask_app, url_prefix=self.url_prefix)
        self.dispatcher.register_adapters(adapters.HalAdapter)

    def get_rule_list(self):
        return [[each.rule, each.endpoint, each.methods] for each in self.app.application.url_map.iter_rules()]


    def test_hypermedia_shopping_basket(self):
        """
        A hypermedia example that simulates a shopping basket with relatingships. The basket is a 'collection'
        while it contains individual items.

        First Verification: The collection has a trailing '/', the items don't.
        Second Assertion: The created links are callable.


        :return:
        """

        class Hierarchy():
            @classproperty
            def base_url(cls):
                """
                Gets the base_url for the resource
                This is prepended to all routes indicated
                by an apimethod decorator.

                :return: The base_url for the resource(s)
                :rtype: unicode
                """
                pks = cls.pks[-1:] or []
                parts = ['<{0}>'.format(pk) for pk in pks]
                base_url = join_url_parts(cls.base_url_sans_pks, *parts).strip('/')
                return '/{0}'.format(base_url) if not cls.append_slash else '/{0}/'.format(base_url)



            @classproperty
            def base_url_sans_pks(cls):
                """
                A class property that returns the base url
                without the pks.
                This is just the /{namespace}/{resource_name}

                For example if the _namespace = '/api' and
                the _resource_name = 'resource' this would
                return '/api/resource' regardless if there
                are pks or not.

                :return: The base url without the pks
                :rtype: unicode
                """

                pks = cls.pks[:-1] or [] #only use the last primary key element
                parts = ['<{0}>'.format(pk) for pk in pks]
                base_url = join_url_parts(cls.namespace, cls.resource_name).lstrip('/')
                base_url = join_url_parts(base_url, *parts).strip('/')
                return '/{0}/'.format(base_url) if not cls.append_slash else '/{0}/'.format(base_url)



        #
        #
        # class Shop(Hierarchy, restmixins.RetrieveList, restmixins.Create):
        #     """
        #     The shopping basket which will contain the items
        #
        #     Retrieve: Collection of baskets
        #     Create: New selection into existing or new basket
        #     """
        #     manager = BasketManager
        #     resource_name = 'basket'
        #     # pks = ('basket_key',)
        #     append_slash = True
        #
        #     _relationships = (
        #         Relationship('basket_relation', relation='Basket', property_map=dict(basket_key='basket_key', relation_key='relation_key')),
        #     )
        #


        class BasketCollection(restmixins.RetrieveList):
            manager = BasketManager
            resource_name = 'basket'
            append_slash = True

            _relationships = (
                ListRelationship('baskets_relation', relation='Basket', property_map=dict(basket='basket')),
            )


        class Basket(Hierarchy, restmixins.Create, restmixins.RetrieveList):
            """
            The shopping basket which will contain the items

            Retrieve: Collection of baskets
            Create: New selection into existing or new basket
            """

            manager = BasketManager
            resource_name = 'basket'
            pks = ('basket_key',)
            append_slash = True

            _relationships = (
                ListRelationship('item_relations', relation='ItemSelection', property_map=dict(basket='basket', basket_key='basket_key', relation_key='relation_key')),
                ListRelationship('object', relation='Item'),
            )

        class ItemSelection(Hierarchy, restmixins.CreateRetrieve):
            """
            The link between an Item object and the shopping basket
            'The item is selected to be in this basket'

            Retrieve: Collection of selection items in basket

            """
            manager = BasketManager
            resource_name = 'basket'
            pks = ('basket_key', 'relation_key',)
            # Forced to use property map, otherwise the url is not properly built as the attribute is removed from
            # the list of attributes before the url is built.
            # The following does not work:
            # _relationships = (Relationship('basketid', relation='Basket'),)

            _relationships = (
                Relationship('basket_relation', relation='Basket', property_map=dict(basket_key='basket_key')),
                # Relationship('item_relation', relation='Item')
            )

            append_slash = False  # For clarity - this is the default

        class Item(restmixins.Retrieve):
            resource_name = 'item'
            pks = ('object_id')

        self.dispatcher.register_resources(BasketCollection)
        self.dispatcher.register_resources(Basket)
        self.dispatcher.register_resources(ItemSelection)

        rules = self.get_rule_list()
        rule_list = [x[0] for x in rules]
        # Verify that the rules are created correctly
        self.assertIn('/testing/ripozo/api/v1.0/basket/', rule_list,
                      'The collection of baskets rule has a trailing slash')

        self.assertIn('/testing/ripozo/api/v1.0/basket/<basket_key>/', rule_list,
                      'A specific basket is a collection of items and has a trailing slash')

        self.assertIn('/testing/ripozo/api/v1.0/basket/<basket_key>/<relation_key>', rule_list,
                      'A specific item does not have a trailing slash')

        # Create a new basket and add/select new item 987
        # Returns the created selection object
        data = json.dumps({"object_key": '987'})
        rv_post_new_basket = self.app.post(self.url_prefix+'/basket/', data=data, content_type='application/json')

        self.assertEqual('201 CREATED', rv_post_new_basket.status, 'Successfully Created?')

        return_basket_data = rv_post_new_basket.data.decode('utf-8')

        # Parse return data and extract 'basket relation' and 'self' link of the new item
        return_basket_object = json.loads(return_basket_data)
        basket_link = return_basket_object['_links']['self']['href']
        basket_item_link = return_basket_object['_links']['item_relations'][0]['href']

        # The links must be valid calls
        rv_retrieve_item = self.app.get(basket_item_link) # Call GET with the returned item selection link
        rv_retrieve_item_object = json.loads(rv_retrieve_item.data.decode('utf-8'))
        print("", flush=True)
        rv_retrieve_basket = self.app.get(basket_link) # Call GET with the returned basket link
        rv_retrieve_basket_object = json.loads(rv_retrieve_basket.data.decode('utf-8'))

        print("", flush=True)

        self.assertEqual(self.host+self.url_prefix+'/basket/1/', basket_link)
        self.assertEqual(self.host+self.url_prefix+'/basket/1/1', basket_item_link)

        self.assertEqual('200 OK', rv_retrieve_item.status)

        # Now post a second relation into the same basket
        data = json.dumps({"object_key": '556'})
        rv_post_second_relation = self.app.post(basket_link, data=data, content_type='application/json')

        rv_test = self.app.get(self.host+self.url_prefix+'/basket/')




        print("POST return:")
        pprint(json.loads(return_basket_data))

        rv_retrieve_basket = self.app.get(basket_link) # Call GET with the returned basket link
        rv_retrieve_basket_object = json.loads(rv_retrieve_basket.data.decode('utf-8'))
        print(rv_retrieve_basket_object)


