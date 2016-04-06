import yaml
from objects import Scene, Fixture, Modifier


CONFIG_FILE = "conf.yaml"


def load_data():
    data = yaml.load(open(CONFIG_FILE).read())
    return data

CONFIG = load_data()


def load_fixtures():
    fixtures = {}
    for fixture, values in CONFIG['fixtures'].iteritems():
        fixtures[fixture] = Fixture(fixture, values['start_address'],
                                    values['address_length'])
    return fixtures


def load_scenes(manager):
    scenes = {}
    for scene, data in CONFIG['scenes'].iteritems():
        scenes[scene] = Scene(scene, manager)
        for fixture, fvalues in data['fixtures'].iteritems():
            scenes[scene].add_fixture(fixture, fvalues['values'])
    return scenes
