from pathlib import Path

import pandas as pd
import seaborn as sns

import serial
import numpy as np
import matplotlib.pyplot as plt

import time

from test12 import *

from shiny import App, Inputs, Outputs, Session, reactive, render, ui
import shinyswatch

sns.set_theme(style="white")
ser = serial.Serial()
plot_data = np.zeros(3000)
plot_data = reactive.Value(plot_data)
header = ""
header = reactive.Value(header)
header.set("waiting for data")


def read_data_from_serial(serial_port):
    # Read data from the serial port
    # Reading 6000 16-bit integers (12000 bytes)
    raw_data = serial_port.read(6000)

    if len(raw_data) == 6000:
        # Convert the byte data to integers
        data = []
        temp = raw_data[:200]
        header = ''.join(chr(i) for i in temp)
        for i in range(202, len(raw_data), 2):
            value = int.from_bytes(
                raw_data[i:i+2], byteorder='little', signed=False)
            data.append(value)
        data = np.array(data)
        return [data, header]


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
            id="recv_data",
            label="Receive Data"
        ),
        ui.input_text(
            "integration_time",
            "Integration Time(ms):",
            value=10
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
    shinyswatch.theme.flatly,
    ui.layout_columns(
        ui.card(
            ui.card_header("Received Spectra"),
            # ui.output_plot("plot_fig"),
            ui.card_footer(
                ui.input_action_button(
                    "clear_data",
                    "Clear Data"
                )
            ),
            height="70vh"
        ),
        ui.card(
            ui.card_header("Raw Data"),
            ui.output_text_verbatim(
                "raw_output",
                placeholder=True
            ),
            height="70vh"
        ),
        ui.card(
            ui.card_header("Header Data"),
            ui.output_text_verbatim(
                "header_text",
                placeholder=True
            ),
            height="30vh",
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
        ser = serial.Serial(port, baud, timeout=1)
        pass

    @reactive.effect
    @reactive.event(input.recv_data)
    def read():
        global ser
        global plot_data
        global header
        btn = input.start_serial()
        if btn == 0:
            print("Serial Port not opened")
        else:
            it = input.integration_time()
            s = "START:" + it
            ser.write(s.encode('utf-8'))
            print("sent request for data ", s)
            time.sleep(1)
            if ser.inWaiting():
                print("recieved data")
                data = read_data_from_serial(ser)
                plot_data = data[0]
                header = data[1]
                print(data[0])
                print(header)
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
        global test_data
        btn = input.start_serial()
        if btn > 0:
            return str(test_data)
        return "waiting for data"

    @render.text
    def header_text():
        global header
        return header

    @render.plot
    def plot_fig():
        fig, ax = plt.subplots()
        x = np.arange(3000)  # 6000 data points
        y = np.plot_data  # Initial data
        ax.plot(x, y)

        ax.set_ylim(0, 4096)  # Assuming 12-bit ADC resolution
        ax.set_xlim(0, 3000)
        return fig


app = App(app_ui, server)
