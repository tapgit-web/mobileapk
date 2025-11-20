from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from threading import Thread, Event
import modbus_reader

class ModbusGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=5, **kwargs)

        # --- Input Section ---
        input_layout = GridLayout(cols=2, size_hint_y=None, height=160, row_default_height=40, spacing=5)

        input_layout.add_widget(Label(text="IP Address"))
        self.ip_input = TextInput(multiline=False)
        input_layout.add_widget(self.ip_input)

        input_layout.add_widget(Label(text="Port"))
        self.port_input = TextInput(multiline=False)
        input_layout.add_widget(self.port_input)

        input_layout.add_widget(Label(text="Registers (0|2|4)"))
        self.reg_input = TextInput(multiline=False)
        input_layout.add_widget(self.reg_input)

        self.add_btn = Button(text="Add Device", size_hint_y=None, height=40)
        self.add_btn.bind(on_press=self.add_device)
        input_layout.add_widget(self.add_btn)
        input_layout.add_widget(Label())  # empty cell

        self.add_widget(input_layout)

        # --- Device List ---
        self.devices_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.devices_layout.bind(minimum_height=self.devices_layout.setter('height'))
        device_scroll = ScrollView(size_hint=(1, 0.25))
        device_scroll.add_widget(self.devices_layout)
        self.add_widget(Label(text="Stored Devices"))
        self.add_widget(device_scroll)

        # --- Output Section ---
        self.output_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.output_layout.bind(minimum_height=self.output_layout.setter('height'))
        output_scroll = ScrollView(size_hint=(1, 0.4))
        output_scroll.add_widget(self.output_layout)
        self.add_widget(Label(text="Output"))
        self.add_widget(output_scroll)

        # --- Start / Stop Buttons ---
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=50, spacing=5)
        self.start_btn = Button(text="Start Reading")
        self.start_btn.bind(on_press=self.start_reading)
        self.stop_btn = Button(text="Stop Reading")
        self.stop_btn.bind(on_press=self.stop_reading)
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.stop_btn)
        self.add_widget(btn_layout)

        # --- Load Devices ---
        self.devices = modbus_reader.load_devices()
        self.update_device_list()

        # Thread control
        self.threads = []
        self.stop_events = []

    # --- Device Management ---
    def add_device(self, instance):
        ip = self.ip_input.text.strip()
        port = self.port_input.text.strip()
        regs = self.reg_input.text.strip()

        if not ip or not port or not regs:
            self.append_output("Error: All fields are required!")
            return

        try:
            port = int(port)
            reg_list = [int(r) for r in regs.split("|")]
        except:
            self.append_output("Error: Invalid port or register format!")
            return

        self.devices.append({"ip": ip, "port": port, "registers": reg_list})
        modbus_reader.save_devices(self.devices)
        self.update_device_list()
        self.append_output(f"Device {ip}:{port} added!")

    def update_device_list(self):
        self.devices_layout.clear_widgets()
        for dev in self.devices:
            self.devices_layout.add_widget(Label(text=f"{dev['ip']}:{dev['port']} [{dev['registers']}]"))

    # --- Reading Threads ---
    def start_reading(self, instance):
        self.stop_reading(None)
        for dev in self.devices:
            stop_event = Event()
            self.stop_events.append(stop_event)
            t = Thread(target=self.read_device_thread, args=(dev, stop_event), daemon=True)
            t.start()
            self.threads.append(t)
        self.append_output("Started reading all devices...")

    def stop_reading(self, instance):
        for ev in self.stop_events:
            ev.set()
        self.threads.clear()
        self.stop_events.clear()
        self.append_output("Stopped all devices.")

    def read_device_thread(self, dev, stop_event):
        while not stop_event.is_set():
            out = modbus_reader.read_modbus_device(dev["ip"], dev["port"], dev["registers"])
            Clock.schedule_once(lambda dt, txt=out: self.append_output(txt))
            import time; time.sleep(1)

    # --- Output ---
    def append_output(self, text):
        lbl = Label(text=text, size_hint_y=None)
        lbl.height = max(30, len(text.splitlines()) * 20)
        self.output_layout.add_widget(lbl)

class ModbusApp(App):
    def build(self):
        return ModbusGUI()

if __name__ == "__main__":
    ModbusApp().run()
