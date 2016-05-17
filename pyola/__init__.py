from conf import Config
from objects import FadeScene
from modifiers.utils import cap
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
import time


def DmxSent(state):
    if not state.Succeeded():
        print "We did not succeed this time"


class RatBag(ServerAdapter):
    server = None

    def serve(self, app, **kw):
        _myserver = kw.pop('_server', create_server)
        self.myserver = _myserver(app, **kw)
        self.myserver.run()

    def run(self, handler):
        self.serve(handler, host=self.host, port=self.port, threads=10)


class Manager(object):
    def __init__(self, config_file, no_olad):
        self.no_olad = no_olad
        if not self.no_olad:
            self.wrapper = ClientWrapper()
        else:
            self.wrapper = None
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
                if not self.fixtures[fixture.name].override.get(chan, None):
                    self.fixtures[fixture.name].sliders[chan].set_value(value)

        for fixture_name, fixture in self.fixtures.iteritems():
            # print fixture.values
            for chan, value in fixture.values.iteritems():
                if self.fixtures[fixture.name].override.get(chan, None):
                    value = int(self.fixtures[fixture.name].sliders[chan].get_value())
                chan_value = self.fixtures[fixture.name].chans[chan]
                rdata[fixture.start_address + chan_value - 2] = value
        if not self.no_olad:
            try:
                self.wrapper.Client().SendDmx(1, rdata, DmxSent)
            except:
                st = time.time()
                self.wrapper.Stop()
                self.wrapper = ClientWrapper()
                print "We had to reset"
                print time.time() - st
        GObject.timeout_add(10, self.run)


@route('/boo/')
def getter():
    ddict = {}
    for fixture_name, fixture in manager.fixtures.iteritems():
        vals = {}
        for chan, value in fixture.values.iteritems():
            if fixture.override.get(chan, None):
                value = int(fixture.sliders[chan].get_value())
            vals[chan] = value
        ddict[fixture_name] = vals
    return json.dumps(ddict)


class MyWindow(Gtk.Window):
    def __init__(self, manager):
        self.manager = manager
        self.builder = Gtk.Builder()
        self.builder.add_from_file("pyola.glade")

        window = self.builder.get_object("window1")
        window.set_default_size(800, 600)
        notebook = self.builder.get_object('notebook1')
        button1 = self.builder.get_object("button1")
        submit = self.builder.get_object("submit")

        blal = button1.get_children()[0]
        hb = blal.get_children()[0]
        im, lab = hb.get_children()
        lab.set_label('Reload Config')

        blal = submit.get_children()[0]
        hb = blal.get_children()[0]
        im, lab = hb.get_children()
        lab.set_label('Transition')

        sorted_fixtures = sorted(self.manager.fixtures.keys())
        for fixture in sorted_fixtures:
            self._build_fixture_gui(self.manager.fixtures[fixture], notebook)

        window.show_all()

        handlers = {
            "onDeleteWindow": Gtk.main_quit,
            "onButtonPressed": self.on_button_clicked,
            "onConfigReload": self.on_config_reload,
            "onScrollNotebook": self.on_scroll_notebook
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

    def _build_fixture_gui(self, fixture, notebook):
        sorted_fixture_channels = sorted(fixture.chans.keys(), key=lambda a: fixture.chans[a])

        fixture_hbox = Gtk.HBox(homogeneous=True)
        fixture_hbox.set_hexpand(False)
        for chan in sorted_fixture_channels:
            chan_label = Gtk.Label(chan)
            chan_vbox = Gtk.VBox()
            chan_vbox.set_homogeneous(False)
            # a vertical scale
            ad2 = Gtk.Adjustment(0, 0, 255, 5, 10, 0)
            chan_slider = Gtk.Scale(
                orientation=Gtk.Orientation.VERTICAL, adjustment=ad2)
            chan_slider.set_inverted(True)
            # that can expand vertically if there is space in the grid (see below)

            # we connect the signal "value-changed" emitted by the scale with the callback
            # function scale_moved
            chan_slider.connect("value-changed", self.chan_slider_moved, fixture, chan)
            chan_slider.set_value(0)
            chan_slider.set_sensitive(False)
            for i in range(0, 2551, 250):
                chan_slider.add_mark(int(i / 10.0), Gtk.PositionType.LEFT, str(int(i / 10.0)))
            fixture.sliders[chan] = chan_slider
            chan_checkbox = Gtk.CheckButton()
            chan_checkbox.set_halign(Gtk.Align.CENTER)
            chan_checkbox.connect("toggled", self.chan_toggled, fixture, chan, chan_slider)
            fixture_label = Gtk.Label(fixture.name)
            fixture_label.set_halign(Gtk.Align.CENTER)
            chan_vbox.pack_start(chan_slider, True, True, 0)
            chan_vbox.pack_start(chan_checkbox, False, False, 0)
            chan_vbox.pack_start(chan_label, False, False, 0)

            fixture_hbox.add(chan_vbox)

        notebook.append_page(fixture_hbox, fixture_label)

    def chan_slider_moved(self, widget, fixture, chan):
        # print fixture, chan
        pass

    def chan_toggled(self, widget, fixture, chan, chan_slider):
        chan_slider.set_sensitive(widget.get_active())
        fixture.override[chan] = widget.get_active()

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

    def on_config_reload(self, widget):
        self.manager._config.config = self.manager._config.load_data()
        self.manager._config.load_scenes(update=True)

    def on_scroll_notebook(self, widget, e):
        if e.get_scroll_deltas()[2] == 1.0:
            widget.next_page()
        else:
            widget.prev_page()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config-file', help='config file', required=True)
    parser.add_argument(
        '--no-olad', action='store_true', default=False,
        help='Disable olad (for testing)')
    args = parser.parse_args()

    manager = Manager(args.config_file, args.no_olad)

    _server = RatBag(host='127.0.0.1', port='8000')
    server_thread = threading.Thread(target=run, kwargs=dict(server=_server, quiet=True))
    # Good for debugging
    # server_thread = threading.Thread(target=run, kwargs=dict(host=self._server_hostname,
    #                                                         port=self._server_port))
    server_thread.daemon = True
    server_thread.start()

    GObject.timeout_add(10, manager.run)
    Gtk.main()
