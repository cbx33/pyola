from conf import load_fixtures, load_scenes, load_fixture_types, load_default_scene
from objects import FadeScene
import array
from ola.ClientWrapper import ClientWrapper

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

wrapper = ClientWrapper()


def DmxSent(state):
    if not state.Succeeded():
        wrapper.Stop()


class Manager(object):
    def __init__(self):
        self.fixture_types = load_fixture_types()
        self.fixtures = load_fixtures(self.fixture_types)
        self.scenes = load_scenes(self)
        self.set_scene(self.scenes[load_default_scene()])

    def set_scene(self, scene, reset=True):
        self.current_scene = scene
        if reset:
            self.current_scene.reset()
        if hasattr(self, 'win'):
            source = self.win.builder.get_object('source')
            model = source.get_model()
            for i, item in enumerate(model):
                if item[0] == self.current_scene.name:
                    source.set_active(i)


    def run(self):
        rdata = array.array('B')
        for i in range(0, 512):
            rdata.append(0)

        # Use the scene to set the fixtures values
        for fixture, values in self.current_scene.fixtures.iteritems():
            for chan, value in values.iteritems():
                # chan_value = self.fixtures[fixture.name].chans[chan]
                self.fixtures[fixture.name].values[chan] = value

        for fixture_name, fixture in self.fixtures.iteritems():
            print fixture.values
            for chan, value in fixture.values.iteritems():
                chan_value = self.fixtures[fixture.name].chans[chan]
                rdata[fixture.start_address + chan_value - 2] = value
        wrapper.Client().SendDmx(1, rdata, DmxSent)
        GObject.timeout_add(10, self.run)


class MyWindow(Gtk.Window):
    def __init__(self, manager):
        self.manager = manager
        self.builder = Gtk.Builder()
        self.builder.add_from_file("pyola.glade")

        window = self.builder.get_object("window1")
        window.show_all()

        handlers = {
            "onDeleteWindow": Gtk.main_quit,
            "onButtonPressed": self.on_button_clicked
        }
        self.builder.connect_signals(handlers)

        source_store = Gtk.ListStore(str)
        scenes = manager.scenes.keys()
        for scene in scenes:
            source_store.append([scene])
        source = self.builder.get_object('source')
        source.set_model(source_store)
        renderer_text = Gtk.CellRendererText()
        source.pack_start(renderer_text, True)
        source.add_attribute(renderer_text, "text", 0)
        for i, item in enumerate(source_store):
            if item[0] == self.manager.current_scene.name:
                source.set_active(i)


        destination_store = Gtk.ListStore(str)
        scenes = manager.scenes.keys()
        for scene in scenes:
            destination_store.append([scene])
        destination = self.builder.get_object('destination')
        destination.set_model(destination_store)
        renderer_text = Gtk.CellRendererText()
        destination.pack_start(renderer_text, True)
        destination.add_attribute(renderer_text, "text", 0)

    def on_button_clicked(self, widget):
        source = self.builder.get_object('source')
        tree_iter = source.get_active_iter()
        if tree_iter:
            model = source.get_model()
            source_s = model[tree_iter][0]
        destination = self.builder.get_object('destination')
        tree_iter = destination.get_active_iter()
        if tree_iter:
            model = destination.get_model()
            destination_s = model[tree_iter][0]

        timeout = float(self.builder.get_object('timeout').get_text())
        trans_scene = FadeScene(
            "fade",
            self.manager,
            self.manager.scenes[source_s],
            self.manager.scenes[destination_s],
            timeout)
        manager.set_scene(trans_scene)


if __name__ == "__main__":
    manager = Manager()
    win = MyWindow(manager)
    manager.win = win
    #manager.set_scene(manager.scenes['black'])
    GObject.timeout_add(10, manager.run)
    Gtk.main()
