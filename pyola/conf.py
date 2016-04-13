import yaml
from objects import Scene, Fixture, FixtureType, mod_map


CONFIG_FILE = "conf.yaml"


def load_data():
    data = yaml.load(open(CONFIG_FILE).read())
    return data

CONFIG = load_data()


def load_default_scene():
    return CONFIG['start_scene']


def load_constants():
    return CONFIG['constants']


def load_fixture_types():
    fixture_types = {}
    for fixture_type, values in CONFIG['fixture_types'].iteritems():
        fixture_types[fixture_type] = FixtureType(
            fixture_type, values['address_length'], values['chans']
        )
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
    for scene_name, data in CONFIG['scenes'].iteritems():
        scene = Scene(scene_name, manager, data)
        scenes[scene_name] = scene
        for fixture, fvalues in data['fixtures'].iteritems():
            new_values = {}
            for chan, value in fvalues['values'].iteritems():
                if isinstance(value, int):
                    new_values[chan] = value
                elif isinstance(value, basestring):
                    new_values[chan] = manager.constants[value]
                else:
                    new_values[chan] = mod_map[value['type']](
                        "{}-{}-{}".format(scene, fixture, chan), scene, value, manager)
            scene.add_fixture(manager.fixtures[fixture], new_values)
        if 'modifiers' in data:
            for modifier, m_data in data['modifiers'].iteritems():
                scene.modifiers.append(
                    mod_map[m_data['type']](modifier, scene, m_data, manager, mode="global")
                )
    return scenes
