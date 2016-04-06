import yaml
from objects import Scene, Fixture, Modifier, FixtureType


CONFIG_FILE = "conf.yaml"


def load_data():
    data = yaml.load(open(CONFIG_FILE).read())
    return data

CONFIG = load_data()


def load_fixture_types():
    fixture_types = {}
    for fixture_type, values in CONFIG['fixture_types'].iteritems():
        fixture_types[fixture_type] = FixtureType(fixture_type, values['address_length'], values['chans'])
    return fixture_types


def load_fixtures(fixture_types):
    fixtures = {}
    for fixture, values in CONFIG['fixtures'].iteritems():
        fixture_type = fixture_types[values['type']]
        fixtures[fixture] = Fixture(fixture, values['start_address'],
                                    fixture_type.address_length,
                                    fixture_type.chans)
    return fixtures


def load_scenes(manager):
    scenes = {}
    for scene, data in CONFIG['scenes'].iteritems():
        scenes[scene] = Scene(scene, manager)
        for fixture, fvalues in data['fixtures'].iteritems():
            scenes[scene].add_fixture(manager.fixtures[fixture], fvalues['values'])
    return scenes
