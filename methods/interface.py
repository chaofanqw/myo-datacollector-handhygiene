import sys
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QComboBox, \
    QLineEdit, QVBoxLayout, QMessageBox, QHBoxLayout, \
    QLabel, QPushButton
from PyQt5.QtCore import Qt
import methods.vlc_player as vlc_player
import methods.poster as poster
import methods.collect_data as collect_data
import myo
from multiprocessing import Process, Pipe
import os

"""
In Windows, please install vlc(x64) from https://www.videolan.org/vlc/download-windows.html ,
and set the environment path: PYTHON_VLC_MODULE_PATH: C:\Program Files\VideoLAN\VLC or other installed path;

In MacOS, it will be necessary install vlc by homebrew, with
brew cask install vlc
"""


class HandWashingCollector(QWidget):

    def __init__(self, pipe):
        super().__init__()

        self.pipe = pipe
        self.position_list = ['left-UpperArm left-LowerArm right-UpperArm',
                              'left-UpperArm left-LowerArm right-LowerArm',
                              'left-UpperArm right-UpperArm right-LowerArm',
                              'left-LowerArm right-UpperArm right-LowerArm']
        self.video_type_list = ['With Demonstration', 'Without Demonstration', 'Poster']
        self.input_width = 300

        self.v_layout = QVBoxLayout()
        self.line_edit = QLineEdit(self)
        self.experiment = QLineEdit(self)
        self.combobox_position = QComboBox(self)
        self.combobox_type = QComboBox(self)
        self.begin_button = QPushButton('Begin Experiment')
        self.begin_button.clicked.connect(self.button_func)

        self.player = []

        self.init_ui()

    def init_ui(self):
        self.layout_init()
        self.combobox_init()

        self.resize(400, 300)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topRight())
        self.setWindowTitle('Hand Washing Experiment')

        self.show()

    def layout_init(self):
        experiment_box = QHBoxLayout()
        experiment_box.addWidget(QLabel('Participant Name:'))
        self.line_edit.setFixedWidth(self.input_width)
        experiment_box.addWidget(self.line_edit, alignment=Qt.AlignHCenter)
        self.v_layout.addLayout(experiment_box)

        name_box = QHBoxLayout()
        name_box.addWidget(QLabel('Experiment Times:'))
        self.experiment.setFixedWidth(self.input_width)
        name_box.addWidget(self.experiment, alignment=Qt.AlignHCenter)
        self.v_layout.addLayout(name_box)

        position_box = QHBoxLayout()
        position_box.addWidget(QLabel('Armband Position:'))
        self.combobox_position.setFixedWidth(self.input_width)
        position_box.addWidget(self.combobox_position, alignment=Qt.AlignHCenter)
        self.v_layout.addLayout(position_box)

        type_box = QHBoxLayout()
        type_box.addWidget(QLabel('Display Type:'))
        self.combobox_type.setFixedWidth(self.input_width)
        type_box.addWidget(self.combobox_type, alignment=Qt.AlignHCenter)
        self.v_layout.addLayout(type_box)

        self.v_layout.addWidget(self.begin_button)

        self.setLayout(self.v_layout)

    def combobox_init(self):
        self.combobox_position.addItems(self.position_list)
        self.combobox_type.addItems(self.video_type_list)

    def button_func(self):
        if str(self.line_edit.text()) == '' or str(self.experiment.text()) == '':
            warning_box = QMessageBox()
            warning_box.setText('Please enter the participant\'s name\nand the experiment times')
            warning_box.setStandardButtons(QMessageBox.Ok)
            warning_box.exec()
        else:
            if 'Demonstration' in (str(self.combobox_type.currentText())):
                player = vlc_player.Player()
                player.set_pipe(self.pipe)
                self.pipe.send({'status': 'start', 'participant_name': str(self.line_edit.text()),
                                'experiment_times': str(self.experiment.text()),
                                'position': str(self.combobox_position.currentText()),
                                'video_type': str(self.combobox_type.currentText())})
                self.player.append(player)
                player.show()
                player.resize(1200, 800)

                if (str(self.combobox_type.currentText())) == 'With Demonstration':
                    player.OpenFile('../resource/Video_withDemon.mp4')
                else:
                    player.OpenFile('../resource/Video_withoutDemon.mp4')
            else:
                video = self.create_dir() + 'video.avi'
                handwashing_poster = poster.Poster(video)
                handwashing_poster.set_pipe(self.pipe)
                self.pipe.send({'status': 'start', 'participant_name': str(self.line_edit.text()),
                                'experiment_times': str(self.experiment.text()),
                                'position': str(self.combobox_position.currentText()),
                                'video_type': str(self.combobox_type.currentText())})
                self.player.append(handwashing_poster)
                handwashing_poster.show()

    def create_dir(self):
        data_path = '../data/'
        data_path_participant = data_path + 'person-' + str(self.line_edit.text()) + '/'
        data_path_participant_record = data_path_participant + 'Experiment-' + str(self.experiment.text()) + '/'

        if not os.path.exists(data_path):
            os.mkdir(data_path)

        if not os.path.exists(data_path_participant):
            os.mkdir(data_path_participant)

        if not os.path.exists(data_path_participant_record):
            os.mkdir(data_path_participant_record)

        return data_path_participant_record

def plot_emg(pipe):
    if sys.platform.startswith('win'):
        path = '../myo_sdk/sdk_windows'
    elif sys.platform.startswith('darwin'):
        path = '../myo_sdk/sdk_macos'

    myo.init(sdk_path=path)
    hub = myo.Hub()
    listener = collect_data.DataCollector(512)
    with hub.run_in_background(listener.on_event):
        collect_data.Plot(listener).data_plot(pipe)


def interface(pipe):
    app = QApplication(sys.argv)
    collector = HandWashingCollector(pipe)
    sys.exit(app.exec_())


def main():
    pipe_emg, pip_interface = Pipe()

    process_emg = Process(target=plot_emg, args=(pipe_emg,))
    process_interface = Process(target=interface, args=(pip_interface,))
    process_emg.start()
    process_interface.start()
    process_emg.join()
    process_interface.join()


if __name__ == '__main__':
    main()
