from copy import deepcopy
import yaml

from objects import Scene, Fixture, FixtureType
from modifiers import mod_map
from modifiers.utils import get_val_from_const


CONFIG_FILE = "conf.yaml"

from collections import Mapping


def recursive_update(orig_dict, updates):
    """
    Update dict objects with recursive merge.
    Args:
        orig_dict: The original dict.
        updates: The updates to merge with the dictionary.
    """
    for key, val in updates.iteritems():
        # If the item with update is a mapping, let's go deeper
        if isinstance(val, Mapping):
            orig_dict[key] = recursive_update(orig_dict.get(key, {}), val)
        # If the thing updated is a list and the update is also a list, then just extend it
        elif isinstance(val, list) and isinstance(orig_dict.get(key, None), list):
            # lists are treated as leaves of the update functions.
            # Things would get waaay to complicated.
            orig_dict[key].extend(val)
        # Otherwise if we are updating a dictionary and no previous branch matched, just set it.
        elif isinstance(orig_dict, Mapping):
            orig_dict[key] = updates[key]
        else:
            orig_dict = {key: updates[key]}
    return orig_dict


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
            else:
                val_dict[chan] = mod_map[value['type']](
                    "{}-{}-{}".format(scene, fixture, chan), scene, value, self.manager)
            print val_dict
        return val_dict

    def load_scenes(self, update=False):
        scenes = {}
        for scene_name, data in self.config['scenes'].iteritems():
            print scene_name
            while "inherit" in data:
                inherit_data = deepcopy(self.config['scenes'][data['inherit']])
                print "INHERIT", inherit_data
                update_data = deepcopy(data)
                print "ORIGINAL", update_data
                update_data.pop('inherit')
                data = recursive_update(inherit_data, update_data)
                print "FINAL", data
                for fixture, fvalues in data['fixtures'].iteritems():
                    if "inherit" in fvalues:
                        fvalues['values'] = {}
            if update and scene_name in self.manager.scenes:
                scene = self.manager.scenes[scene_name]
            else:
                scene = Scene(scene_name, self.manager, data)
                scenes[scene_name] = scene
            if "default_trans" in data:
                scene.default_trans = data['default_trans']
            for fixture, fvalues in data['fixtures'].iteritems():
                new_values = {}
                data2 = deepcopy(fvalues)
                while "inherit" in data2:
                    data2.pop('inherit')
                    print "====== values from inherit ======", fixture
                    inherit_name = fvalues['inherit']
                    inherit_values = data['fixtures'][inherit_name]['values']
                    data2 = data['fixtures'][inherit_name]
                    new_values = self._load_fixtures_values(
                        inherit_values, new_values, scene, fixture)
                if "values" in fvalues:
                    print "====== values from original =======", fixture, fvalues
                    new_values = self._load_fixtures_values(
                        fvalues['values'], new_values, scene, fixture)
                    print "----------", new_values
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
