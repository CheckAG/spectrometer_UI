from pathlib import Path

import pandas as pd
import seaborn as sns

import serial
import numpy as np
import matplotlib.pyplot as plt

import time


from shiny import App, Inputs, Outputs, Session, reactive, render, ui

sns.set_theme(style="white")
ser = serial.Serial()
plot_data = []

def read_data_from_serial(serial_port):
    # Read data from the serial port
    # Reading 6000 16-bit integers (12000 bytes)
    raw_data = serial_port.read(6000)

    if len(raw_data) == 6000:
        # Convert the byte data to integers
        data = []
        for i in range(0, len(raw_data), 2):
            value = int.from_bytes(
                raw_data[i:i+2], byteorder='little', signed=False)
            data.append(value)
        return data


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_action_button(
            "start_serial",
            "Begin Serial"
        ),
        ui.input_text(
            "com_port",
            "COM Port:",
            placeholder="COM15"
        ),
        ui.input_text(
            "baudrate",
            "Baud Rate:",
            value=115200
        ),
        ui.input_action_button(
            id = "recv_data",
            label = "Receive Data"
        ),
        ui.input_text(
            "integration_time",
            "Integration Time(ms):"
        ),
        ui.input_action_button(
            "set_integ_time",
            "Set Integration Time"
        ),
        ui.input_action_button(
            "continuous_mode",
            "Continuous Mode"
        )
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Received Spectra"),
            ui.output_plot("plot_fig"),
            ui.card_footer(
                        ui.input_action_button(
                            "clear_data",
                            "Clear Data"
                        )
                    ),
            height= "70vh"
        ),
        ui.card(
            ui.card_header("Raw Data"),
            ui.output_text_verbatim(
                "raw_output",
                placeholder=True
            ),
            height = "70vh"
        )
    ),
    ui.card(
        ui.card_header("Set Clocks"),
        ui.layout_columns(
            ui.input_action_button(
                "set_sh",
                "Set SH Clock"
            ),
            ui.input_text(
                "sh_period",
                "Period:"
            ),
            ui.input_text(
                "sh_pulse",
                "Pulse:"
            ),
            ui.input_action_button(
                "set_icg",
                "Set ICG Clock"
            ),
            ui.input_text(
                "icg_period",
                "Period:"
            ),
            ui.input_text(
                "icg_pulse",
                "Pulse:"
            ),
            ui.input_action_button(
                "set_master",
                "Set Master Clock"
            ),
            ui.input_text(
                "master_period",
                "Period:"
            ),
            ui.input_text(
                "master_pulse",
                "Pulse:"
            ),
            col_widths=(4,4,4)
        )
    )

)


def server(input: Inputs, output: Outputs, session: Session):

    @reactive.effect    
    @reactive.event(input.start_serial)
    def beginSerial():
        global ser
        port = input.com_port()
        baud = input.baudrate()
        ser = serial.Serial(port,baud,timeout=1)     

    @reactive.effect
    @reactive.event(input.recv_data)
    def read():
        global ser
        global plot_data
        btn = input.start-serial()
        if btn == 0:
            print("Serial Port not opened")
        else:
            it = input.integration_time()
            s = "START:" + it
            ser.write(s.encode('utf-8'))
            time.sleep(1)
            if ser.inWaiting():
                plot_data = read_data_from_serial(ser)
            else:
                print(f"Sent {s}, No Data Recieved")

    @reactive.effect
    @reactive.event(input.set_integ_time)
    def sendIntegrationTime():
        global ser
        int_time = input.integration_time()
        s = "IT:" + int_time
        btn = input.start_serial()
        if btn > 0 and ser.available():
            ser.write(s.encode('utf-8'))

    @reactive.effect
    @reactive.event(input.continuous_mode)
    def sendContinuous():
        print("Not Implemented")
        pass

    @render.text
    def raw_output():
        global ser
        btn = input.start_serial()
        if btn > 0 and ser.available():
            cursor_pos = ser.tell()
            data = ser.readlines()
            ser.seek(cursor_pos)
            return data
        

app = App(app_ui, server)
