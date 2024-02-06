import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QMetaMethod, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTableWidgetItem,
    QWidget,
)
from qt_material import apply_stylesheet

from joystick_diagrams import app_init
from joystick_diagrams.app_state import AppState
from joystick_diagrams.db.db_device_management import add_update_device_template_path
from joystick_diagrams.export import export
from joystick_diagrams.ui.mock_main.qt_designer import export_ui

_logger = logging.getLogger(__name__)


@dataclass
class DeviceTemplate:
    guid: str
    name: str
    path: Path


class ExportPage(QMainWindow, export_ui.Ui_Form):  # Refactor pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.appState = AppState()
        self.ExportButton.clicked.connect(self.run_exporter)

        self.tableWidget.itemClicked.connect(self.device_template_item_clicked)
        self.pushButton.clicked.connect(self.select_template)

        # UI Setup
        self.setup_device_table_widget()

    # Devices WIdget
    def setup_device_table_widget(self):
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.add_device_templates_to_widget()

    def add_device_templates_to_widget(self):
        ## Show the devices / mix of stored and new devices
        widgets = [
            DeviceTemplate(
                "666ec0a0-556b-11ee-8002-44455354000", "My Long Joystick Name (ABS)", "wwwwwwwwwwwwwwwwwwwwwwwwwww"
            ),
            DeviceTemplate("666ec0a0-556b-11ee-8002-44455354000", "2222", "wwwwwwwwwwwwwwwwwwwwwwwwwww"),
            DeviceTemplate("666ec0a0-556b-11ee-8002-44455354000", "3333", None),
        ]
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setHorizontalHeaderLabels(["Device ID", "Device Name", "Template"])

        for index, item in enumerate(widgets):
            self.tableWidget.insertRow(index)

            self.tableWidget.setItem(index, 0, QTableWidgetItem(item.guid))
            self.tableWidget.setItem(index, 1, QTableWidgetItem(item.name))
            self.tableWidget.setItem(index, 2, QTableWidgetItem(item.path))

        self.pushButton.setText("Select Item")
        self.pushButton.setDisabled(True)

    def device_template_item_clicked(self, item):
        item_row_index = item.row()

        device_guid = self.tableWidget.item(item_row_index, 0).text()
        template_path = self.tableWidget.item(item_row_index, 2).text()

        self.pushButton.setDisabled(False)
        if not template_path:
            self.pushButton.setText("Select Template")
        else:
            self.pushButton.setText("Change Template")

    def select_template(self):
        _file = QFileDialog.getOpenFileName(
            self,
            caption="Select an SVG file to use as a template",
            filter=("SVG Files (*.svg)"),
        )
        if _file[0]:
            file_path = Path(_file[0])
            print(file_path)
            self.set_template_for_device(file_path)

    def set_template_for_device(self, template_path: Path):
        selected_table_rows = self.tableWidget.selectionModel().selectedRows()

        # Selection Mode is single so force select first
        if not selected_table_rows:
            return  # Add handling here...

        row_to_modify = selected_table_rows[0].row()
        device_guid = self.tableWidget.item(row_to_modify, 0).text()

        print(f"Modifying row {row_to_modify} for guid {device_guid}")

        # Save the device information
        _save = add_update_device_template_path(device_guid, template_path.__str__())

        if _save:
            self.tableWidget.setItem(row_to_modify, 2, QTableWidgetItem(template_path.__str__()))

    def run_exporter(self):
        for profile in self.appState.processedProfileObjectMapping.values():
            export(profile)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ExportPage()
    window.show()
    apply_stylesheet(app, theme="dark_blue.xml", invert_secondary=False)
    app.exec()
