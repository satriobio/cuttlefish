import os    
import random
import string

import minknow_api
from minknow_api.manager import Manager
from minknow_api.tools.protocols import CriteriaValues
from minknow_api.examples.manage_simulated_devices import *
import panel as pn
import panel.widgets as widgets
import threading
import webview

os.environ["MINKNOW_TRUSTED_CA"] = "/opt/ont/minknow/conf/rpc-certs/ca.crt"

pn.extension(notifications=True)
pn.extension(raw_css=["""
    .bk-header { width: 100px; }
    .mdc-dialog__content { background-color: white; }
    """]
)
pn.config.browser_info = False


class SetupPage:
    def __init__(self):
        
        self.manager = Manager()
        self.positions = self.render_positions()
        
        self.tabs = pn.Tabs(tabs_location='above', sizing_mode='stretch_both')
        self.tabs.append(('Details',self.render_tool_details()))
        self.tabs.append(('Run Until',self.render_tool_rununtil()))

        self.simulate_mini = pn.widgets.Button(name='Simulate', button_type='primary', icon='cube')
        self.simulate_mini.on_click(self.add_simulated_device_mini)

        # self.simulate_prom = pn.widgets.Button(name='Simulate PromethION', button_type='primary', icon='cube')
        # self.simulate_prom.on_click(self.add_simulated_device_prom)

        self.btn_refresh = pn.widgets.Button(name='Refresh', button_type='primary', icon='reload')
        self.btn_refresh.on_click(self.refresh_devices)

        self.layout = self.render_layout()
    
    def render_positions(self):
        positions = list(self.manager.flow_cell_positions())

        device = pn.Column()
        
        for index, position in enumerate(positions):
            if position.is_simulated:
                if position.name[0] == 'M' or position.name[0] == 'X':
                    logo = 'assets/min_sim.webp'
                if position.name[0] == 'P' or isinstance(position.name[0], (int, float)):
                    logo = 'assets/prom_sim.webp'
                else:
                    logo = 'assets/other_sim.webp'
            else:
                if position.name[0] == 'M' or position.name[0] == 'X':
                    logo = 'assets/min.webp'
                if position.name[0] == 'P' or isinstance(position.name[0], (int, float)):
                    logo = 'assets/prom.webp'
                else:
                    logo = 'assets/other.webp'
            
            btn_open = pn.widgets.Button(name='', button_type='primary', icon='folder-open')
            btn_open.on_click(lambda event, idx=index: self.render_flowcell(positions[idx]))

            device.append(pn.Card(
                    pn.Row(
                        
                        pn.Column(pn.panel(logo, height=70)),
                        pn.Column(
                            f'''
                            **{position.name}**
                            State: {position.state}
                            Simulated: {position.is_simulated}
                            ''',
                            sizing_mode='stretch_width'
                        ),
                        pn.Column(
                           btn_open
                        )
                    ),
                    hide_header=True,
                    sizing_mode='stretch_width'
                ))
        return device

    def render_flowcell(self, position):
        self.device = position.name[0]
        self.position = position

        self.btn_play  = pn.widgets.Button(name='', button_type='success', icon='player-play')
        self.btn_play.on_click(self.resume_protocol)

        self.btn_pause = pn.widgets.Button(name='', button_type='warning', icon='player-pause')
        self.btn_pause.on_click(self.pause_protocol)

        self.btn_stop = pn.widgets.Button(name='', button_type='danger', icon='player-stop')
        self.btn_pause.on_click(self.stop_protocol)
        flowcell = pn.Card(
                    f'''
                    # Flow Cell
                    **{position.name}**
                    State: {position.state}
                    Simulated: {position.is_simulated}
                    ''',
                    pn.Row(
                        self.btn_play,
                        self.btn_pause,
                        self.btn_stop,
                    ),
                    pn.Row(
                        self.tabs
                    ),
                    hide_header=True,
                    sizing_mode='stretch_width'
                )

        self.layout[1] = flowcell
    
    def render_tool_rununtil(self):
        self.input_run_limit  = widgets.IntInput(name='Run limit (Hrs)', start=0, step=1)
        self.input_data_limit = widgets.IntInput(name='Data Target (GB)', start=0, step=1)
        self.input_pore_limit = widgets.IntInput(name='Pore Number', start=0, step=1)
        self.input_action     = widgets.RadioButtonGroup(name='Radio Button Group', options=['Pause', 'Stop'])
        
        btn_submit = widgets.Button(name='Submit', button_type='primary')
        btn_submit.on_click(self.submit_run_until)

        card = pn.Card(
                pn.WidgetBox(
                    '''
                    # Run Until
                    ''',
                    pn.pane.Markdown("Action", margin=(0, 0, 0, 12)),
                    self.input_action,
                    self.input_run_limit,
                    self.input_data_limit,
                    self.input_pore_limit,
                    btn_submit,
                    sizing_mode='stretch_width'
                ),
                hide_header=True,
                styles={'box-shadow': 'none', 'border': 'none'}
            )
        return card
    
    def render_tool_details(self):

        obj = {''}
        card = pn.Card(
                pn.WidgetBox(
                    '''
                    # Details
                    No protocol running.
                    ''',
                    sizing_mode='stretch_width'
                ),
                hide_header=True,
                styles={'box-shadow': 'none', 'border': 'none'}
            )

        try:
            connection = self.position.connect()
            obj = connection.protocol.get_current_protocol_run()
            connection.protocol.resume_protocol()
            # pn.state.notifications.success('Protocol Resumed', duration=2000)
            card = pn.Card(
                pn.WidgetBox(
                    '''
                    # Details
                    ''',
                    pn.pane.JSON(obj, name='JSON'),
                    sizing_mode='stretch_width'
                ),
                hide_header=True,
                styles={'box-shadow': 'none', 'border': 'none'}
            )
        except Exception as err:
            pn.state.notifications.warning(str(err), duration=2000)

        
        return card

    def add_simulated_device_mini(self, event):
        pattern = "MS{:05}"
        device_names = None

        create_devices(manager = self.manager, device_names=device_names, pattern=pattern, device_type=minknow_api.manager_pb2.SimulatedDeviceType.SIMULATED_MINION)
    
    def add_simulated_device_prom(self, event):
        pattern = "{}{}"
        device_names = None

        create_devices(manager = self.manager, device_names=device_names, pattern=pattern, device_type=minknow_api.manager_pb2.SimulatedDeviceType.SIMULATED_PROMETHION)

    def refresh_devices(self, event):
        self.layout[0][-1] = self.render_positions()
    
    def resume_protocol(self, event):
        try:
            connection = self.position.connect()
            run = connection.protocol.get_current_protocol_run()
            run.run_id
            connection.protocol.resume_protocol()
            pn.state.notifications.success('Protocol Resumed', duration=2000)
        except Exception as err:
            pn.state.notifications.warning(str(err.details()), duration=2000)

    def pause_protocol(self, event):
        try:
            connection = self.position.connect()
            connection.protocol.pause_protocol()
            pn.state.notifications.success('Protocol Paused', duration=2000)
        except Exception as err:
            pn.state.notifications.warning(str(err.details()), duration=2000)

    def stop_protocol(self, event):
        try:
            connection = self.position.connect()
            connection.protocol.stop_protocol()
            pn.state.notifications.success('Protocol Stopped', duration=2000)
        except Exception as err:
            pn.state.notifications.warning(str(err.details()), duration=2000)

    def submit_run_until(self, event):
        try:
            criteria_args = {}
            target_criteria = {}

            if self.input_run_limit.value > 0:
                criteria_args['runtime'] = self.input_run_limit

            if self.input_pore_limit.value > 0:
                if self.device == 'M' or self.device == 'X':
                    calc = self.input_pore_limit / 2048 
                if self.device == 'P' or isinstance(self.device, (int, float)):
                    calc = self.input_pore_limit / 12000
                else:
                    raise Exception("Sorry, unknown device.")
                
                criteria_args['available_pores'] = calc

            criteria = CriteriaValues(**criteria_args)
            
            if self.input_action.value == 'Pause':
                target_criteria['pause_criteria'] = criteria.as_protobuf()
            
            if self.input_action.value == 'Stop':
                target_criteria['stop_criteria'] = criteria.as_protobuf()
            
            connection = self.position.connect()
            run = connection.protocol.get_current_protocol_run()
            acquisition_run_id = run.acquisition_run_ids[-1]
            connection.run_until.write_target_criteria(acquisition_run_id=acquisition_run_id, **target_criteria)
        except Exception as err:
            pn.state.notifications.warning(str(err.details()), duration=2000)

    def render_layout(self):
        layout = pn.Row(
            pn.Column(
                pn.Card(
                    '''
                    # Devices
                    ''',
                    sizing_mode='stretch_width',
                    hide_header=True,
                ),
                pn.Row(
                    self.simulate_mini,
                    # self.simulate_prom,
                    self.btn_refresh,
                    sizing_mode='stretch_width'
                ),
            self.positions,
            sizing_mode='stretch_width',
            ),
            pn.Column(
                pn.Card(
                    '''
                    # Flow Cell
                    No flow cell selected
                    ''',
                    hide_header=True,
                    sizing_mode='stretch_width'
                ),
            )
        )

        return layout

class PlotApp:
    def __init__(self):
        self.machine_ip = None

        self.connect_button = pn.widgets.Button(name='Connect', button_type='primary', sizing_mode='stretch_width')
        self.connect_button.on_click(self.show_modal)

        self.msg = pn.pane.Markdown("No data available")

        self.sidebar = pn.Column(
            self.connect_button,
            self.msg,
        )
        self.template = pn.template.MaterialTemplate(title='Cuttlefish', sidebar=self.sidebar, collapsed_sidebar=True)

        self.tabs = pn.Tabs(closable=False, sizing_mode='stretch_width')

        self.template.main.append(self.tabs)
        self.tabs.append(('About', self.page_about()))
        self.tabs.append(('Main', self.page_cuttlefish()))
        # self.tabs.append(('Settings', self.page_settings()))
        # self.tabs.append(('Help', self.page_help()))

        self.modal_content = pn.Column(
            pn.pane.Markdown("# Connect to Machine"),
            pn.widgets.TextInput(name='URL/IP', placeholder='Enter URL or IP here ...', sizing_mode='stretch_width'),
            pn.widgets.Button(name='Connect', button_type='primary'),
            width=400
        )
        self.modal_content[1].param.watch(self.set_value, 'value')
        self.modal_content[-1].on_click(self.load_data)
        self.template.modal.append(self.modal_content)
    
    def page_about(self):
        about_text = """
        ## About Cuttlefish
        Cuttlefish is an application to help you adjust ONT sequencing on the fly (or on the swim).
        """
        return pn.Column(pn.panel('assets/logo.gif', height=300), pn.pane.Markdown(about_text))

    def page_cuttlefish(self):
        setup_page = SetupPage()
        return setup_page.layout

    def page_settings(self):

        settings_text = """
        ## Settings
        This application allows you to load and analyze squiggle data.
        """
        return pn.pane.Markdown(settings_text)
    
    def page_help(self):
        
        help_text = """
        ## Help
        This application allows you to load and analyze squiggle data.
        """
        return pn.pane.Markdown(help_text) 

    def show_modal(self, event):
        self.template.open_modal()

    def set_value(self, event):
        self.machine_ip = event.new

    def load_data(self, event):
        self.template.close_modal()
        try:
            self.machine_ip
            setup_page = SetupPage()
            self.tabs[1]((f'Main', setup_page.layout))

            pn.state.notifications.success('Machine connected successfully.', duration=2000)
        except Exception as e:
            pn.state.notifications.warning('An error occurred: {e}', duration=2000)
            pn.state.notifications.warning('Machine connection failed.', duration=2000)

    def servable(self):
        return self.template.servable()

app = PlotApp()

def start_panel():
    pn.serve(app.template, port=5006, show=False)
    app.show_modal()

t = threading.Thread(target=start_panel)
t.daemon = True
t.start()

__VERSION__ = 0.1
try:
    webview.create_window(f'Cuttlefish v{__VERSION__}', 'http://localhost:5006', min_size=(800, 600))
    webview.start()
    print('Webview started!')
except Exception as err:
    print(err)
    print('The App still accesible from http://localhost:5006')