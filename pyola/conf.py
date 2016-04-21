import yaml
from objects import Scene, Fixture, FixtureType, mod_map, get_val_from_const


CONFIG_FILE = "conf.yaml"


class Config(object):
    def __init__(self, config_name, manager):
        self.config_name = config_name
        self.config = self.load_data()
        self.manager = manager

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

    def load_fixtures(self):
        fixture_types = self.manager.fixture_types
        fixtures = {}
        for fixture, values in self.config['fixtures'].iteritems():
            fixture_type = fixture_types[values['type']]
            fixtures[fixture] = Fixture(fixture, values['start_address'],
                                        fixture_type.address_length,
                                        fixture_type.chans)
        return fixtures

    def _load_fixtures_values(self, values, val_dict, scene, fixture):
        for chan, value in values.iteritems():
            print fixture, chan, value, "++"
            if isinstance(value, int):
                val_dict[chan] = value
            elif isinstance(value, basestring):
                val_dict[chan] = get_val_from_const(value, self.manager.constants, chan)
                #val_dict[chan] = self.manager.constants[value]
            else:
                val_dict[chan] = mod_map[value['type']](
                    "{}-{}-{}".format(scene, fixture, chan), scene, value, self.manager)
            print val_dict
        return val_dict

    def load_scenes(self):
        scenes = {}
        for scene_name, data in self.config['scenes'].iteritems():
            scene = Scene(scene_name, self.manager, data)
            scenes[scene_name] = scene
            for fixture, fvalues in data['fixtures'].iteritems():
                new_values = {}
                if "inherit" in fvalues:
                    inherit_name = fvalues['inherit']
                    inherit_values = data['fixtures'][inherit_name]['values']
                    new_values = self._load_fixtures_values(
                        inherit_values, new_values, scene, fixture)
                if "values" in fvalues:
                    new_values = self._load_fixtures_values(
                        fvalues['values'], new_values, scene, fixture)
                """
                    for chan, value in fvalues['values'].iteritems():
                        if isinstance(value, int):
                            new_values[chan] = value
                        elif isinstance(value, basestring):
                            new_values[chan] = self.manager.constants[value]
                        else:
                            new_values[chan] = mod_map[value['type']](
                                "{}-{}-{}".format(
                                    scene, fixture, chan), scene, value, self.manager)
                """
                scene.add_fixture(self.manager.fixtures[fixture], new_values)
            if 'modifiers' in data:
                for modifier, m_data in data['modifiers'].iteritems():
                    scene.modifiers.append(
                        mod_map[m_data['type']](
                            modifier, scene, m_data, self.manager, mode="global")
                    )
        return scenes
