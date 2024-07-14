from pathlib import Path

import pandas as pd
import seaborn as sns

import serial
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time

from test12 import *

from shiny import App, Inputs, Outputs, Session, reactive, render, ui
import shinyswatch

sns.set_theme(style="white")
ser = serial.Serial()
plot_data = np.zeros(4900)
plot_data = reactive.Value(plot_data)
header = ""
header = reactive.Value(header)
header.set("waiting for data")

buffer_size = 10000


def read_data_from_serial(serial_port):
    # Read data from the serial port
    # Reading 6000 16-bit integers (12000 bytes)
    raw_data = serial_port.read(buffer_size)

    if len(raw_data) == buffer_size:
        # Convert the byte data to integers
        data = []
        temp = raw_data[:200]
        header = ''.join(chr(i) for i in temp)
        for i in range(200, len(raw_data), 2):
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
            ui.output_plot("plot_fig"),
            ui.card_footer(
                ui.input_action_button(
                    "clear_data",
                    "Clear Data"
                ),
                ui.download_button(
                    "download_spectrum",
                    "Download as CSV"
                )
            ),
            height="70vh"
        ),
        # ui.card(
        #     ui.card_header("Raw Data"),
        #     ui.output_text(
        #         "raw_output"
        #     ),
        #     height="70vh"
        # ),
        ui.card(
            ui.card_header("Header Data"),
            ui.output_text_verbatim(
                "header_text",
                placeholder=True
            ),
            height="30vh",
        ),
        col_widths=(8, 4)
    )
)


def server(input: Inputs, output: Outputs, session: Session):

    @reactive.effect
    @reactive.event(input.start_serial)
    def beginSerial():
        global ser
        port = input.com_port()
        baud = input.baudrate()
        try:
            ser = serial.Serial(port, baud, timeout=1)
        except:
            print("File not found")
            pass
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
                plot_data.set(data[0])
                header.set(data[1])
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

    # @render.text
    # def raw_output():
    #     global ser
    #     global test_data
    #     btn = input.start_serial()
    #     if btn > 0:
    #         return str(plot_data.get())
    #     return "waiting for data"

    @render.text
    def header_text():
        global header
        return str(header.get())

    @render.plot
    def plot_fig():
        # fig, ax = plt.subplots()
        x = np.arange(4900)  # 6000 data points
        plot_data_temp = plot_data.get()
        y = np.array(plot_data_temp)  # Initial data

        line = plt.plot(x, y)
        plt.ylim((0, 4096))  # Assuming 12-bit ADC resolution
        plt.xlim((0, 4900))
        return line

    @render.download(
        filename=lambda: f"Spectrum-{datetime.datetime.now()}.csv"
    )
    def download_spectrum():
        x = np.arange(4900)
        data = plot_data.get()
        temp_df = pd.DataFrame(data={"Frequency": x, "wavelength": data})
        temp_df.to_csv("./temp.csv", sep=",", index=False)
        path = "./temp.csv"
        return path


app = App(app_ui, server)
