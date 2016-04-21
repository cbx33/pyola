from conf import Config
from objects import FadeScene, cap
import array
from ola.ClientWrapper import ClientWrapper
from bottle import run, route, ServerAdapter
from waitress.server import create_server

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

import threading
import json

import argparse

wrapper = ClientWrapper()


def DmxSent(state):
    if not state.Succeeded():
        wrapper.Stop()


class RatBag(ServerAdapter):
    server = None

    def serve(self, app, **kw):
        _myserver = kw.pop('_server', create_server)
        self.myserver = _myserver(app, **kw)
        self.myserver.run()

    def run(self, handler):
        self.serve(handler, host=self.host, port=self.port, threads=10)


class Manager(object):
    def __init__(self, config_file):
        self._config = Config(config_file, self)
        self.fixture_types = self._config.load_fixture_types()
        self.constants = self._config.load_constants()
        self.fixtures = self._config.load_fixtures()
        self.scenes = self._config.load_scenes()
        self.set_scene(self.scenes[self._config.load_default_scene()])
        self.win = MyWindow(self)

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
                self.fixtures[fixture.name].values[chan] = cap(value)

        for fixture_name, fixture in self.fixtures.iteritems():
            # print fixture.values
            for chan, value in fixture.values.iteritems():
                chan_value = self.fixtures[fixture.name].chans[chan]
                rdata[fixture.start_address + chan_value - 2] = value
        wrapper.Client().SendDmx(1, rdata, DmxSent)
        GObject.timeout_add(10, self.run)


@route('/boo/')
def getter():
    ddict = {}
    for fixture_name, fixture in manager.fixtures.iteritems():
        ddict[fixture_name] = fixture.values
    return json.dumps(ddict)


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
        scenes = sorted(scenes)
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
        scenes = sorted(scenes)
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
    parser = argparse.ArgumentParser(
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config-file', help='config file', required=True)
    args = parser.parse_args()

    manager = Manager(args.config_file)

    _server = RatBag(host='127.0.0.1', port='8000')
    server_thread = threading.Thread(target=run, kwargs=dict(server=_server, quiet=True))
    # Good for debugging
    # server_thread = threading.Thread(target=run, kwargs=dict(host=self._server_hostname,
    #                                                         port=self._server_port))
    server_thread.daemon = True
    server_thread.start()

    GObject.timeout_add(10, manager.run)
    Gtk.main()
