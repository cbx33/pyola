import yaml
from objects import Scene, Fixture, FixtureType, mod_map


CONFIG_FILE = "conf.yaml"


class Config(object):
    def __init__(self, config_name):
        self.config_name = config_name
        self.config = self.load_data()

    def load_data(self):
        data = yaml.load(open(self.config_name).read())
        return data

    def load_default_scene(self):
        return self.config['start_scene']

    def load_constants(self):
        return self.config['constants']

    def load_fixture_types(self):
        fixture_types = {}
        for fixture_type, values in self.config['fixture_types'].iteritems():
            fixture_types[fixture_type] = FixtureType(
                fixture_type, values['address_length'], values['chans']
            )
        return fixture_types

    def load_fixtures(self, fixture_types):
        fixtures = {}
        for fixture, values in self.config['fixtures'].iteritems():
            fixture_type = fixture_types[values['type']]
            fixtures[fixture] = Fixture(fixture, values['start_address'],
                                        fixture_type.address_length,
                                        fixture_type.chans)
        return fixtures

    def load_scenes(self, manager):
        scenes = {}
        for scene_name, data in self.config['scenes'].iteritems():
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
