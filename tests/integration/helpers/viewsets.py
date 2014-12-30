__author__ = 'Tim Martin'
from tests.integration.helpers.managers import PersonManager, DummyManager, PaginatedPersonManager, MultipleKeysManager
from cassandra_rest.viewsets.common import CRUD


class PersonViewset(CRUD):
    manager = PersonManager
    pks = ['id']
    pluralization = 'people'


class DummyViewset(CRUD):
    manager = DummyManager
    pks = ['id']
    pluralization = 'dummies'


class PaginatedPersonViewset(PersonViewset):
    resource_name = 'paginated_person'
    pluralization = 'paginated_people'
    manager = PaginatedPersonManager


class MultipleKeysViewset(CRUD):
    manager = MultipleKeysManager
    pks = ['id1', 'id2', 'id3']
    resource_name = 'multiple_key'