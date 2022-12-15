import ftplib
import pickle
import re
import telnetlib

from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.open_prefs()
        self.port = 9993

        # Initialize window properties
        self.title = "HyperDeck Transfer"
        self.width = 640
        self.height = 250
        self.setWindowIcon(QIcon("videocam.svg"))

        # Initialize buttons
        self.btn_add = QPushButton("Add HyperDeck")
        self.btn_add.clicked.connect(self.clk_btn_add)

        self.btn_rm = QPushButton("Remove Selected")
        self.btn_rm.clicked.connect(self.clk_btn_rm)

        self.btn_chg_save = QPushButton("Change Save Location")
        self.btn_chg_save.clicked.connect(self.clk_btn_chg_save)

        self.btn_toggle_transfer = QPushButton("Toggle File Transfer")
        self.btn_toggle_transfer.clicked.connect(self.clk_btn_toggle_transfer)

        self.btn_transfer = QPushButton("Transfer")
        self.btn_transfer.clicked.connect(self.clk_btn_transfer)

        self.btn_reboot = QPushButton("Reboot Selected")
        self.btn_reboot.clicked.connect(self.clk_btn_reboot)

        # Initialize table
        self.table = CustomTableView()
        self.table.model().setHorizontalHeaderLabels(
            ["HyperDeck IP", "Save Location", "Transferred"]
        )

        self.init_ui()

    def init_ui(self):
        # Build UI and show
        self.setWindowTitle(self.title)
        self.resize(self.width, self.height)

        layout = QVBoxLayout()
        layout_top = QHBoxLayout()
        layout_bottom = QHBoxLayout()

        layout_top.addWidget(self.btn_add)
        layout_top.addWidget(self.btn_rm)
        layout_top.addWidget(self.btn_chg_save)
        layout_top.addWidget(self.btn_toggle_transfer)

        layout_bottom.addWidget(self.btn_transfer)
        layout_bottom.addWidget(self.btn_reboot)

        layout.addLayout(layout_top)
        layout.addWidget(self.table)
        layout.addLayout(layout_bottom)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

        self.refresh_table()

    def clk_btn_add(self):
        # Add new HyperDeck
        new_deck, ok = QInputDialog().getText(
            self, "Add new HyperDeck IP", "Add new HyperDeck IP:"
        )

        if ok and valid_ip_address(new_deck):
            self.prefs["deck_ips"].append(new_deck)
            self.prefs["transferred"].append(True)
            self.refresh_table()
            self.update_prefs()
        elif not valid_ip_address(new_deck):
            print("Must enter an IP address")

    def clk_btn_rm(self):
        # Remove selected HyperDeck
        self.table.rm_row()
        self.update_prefs()

    def clk_btn_chg_save(self):
        # Change Save Location
        folder_out = self.save_folder()

        if folder_out:
            self.prefs["save_folder"] = folder_out
            self.refresh_table()
            self.update_prefs()
        else:
            self.prefs["save_folder"] = None
            self.refresh_table()
            self.update_prefs()

    def clk_btn_toggle_transfer(self):
        # Change whether control signal is sent to deck
        try:
            self.prefs["transferred"][
                self.table.selectedIndexes()[0].row()
            ] = not self.prefs["transferred"][self.table.selectedIndexes()[0].row()]
            self.refresh_table()
            self.update_prefs()
        except Exception:
            pass

    def clk_btn_transfer(self):
        tn = telnetlib.Telnet()

        err_count = 0

        if self.prefs["save_folder"] is not None:
            for ii in range(len(self.prefs["deck_ips"])):
                if self.prefs["transferred"][ii]:
                    try:
                        ftp = ftplib.FTP(self.prefs["deck_ips"][ii])
                        ftp.login()

                        ftp.cwd("/3")

                        file_name = self.prefs["save_folder"] + "/" + ftp.nlst()[-1]
                        with open(file_name, "wb") as f:
                            ftp.retrbinary("RETR " + ftp.nlst()[-1], f.write)
                    except Exception:
                        err_count = err_count + 1

        if err_count == 0:
            QMessageBox.about(self, "Process Complete", "Process has been completed")
        else:
            QMessageBox.about(
                self, "We had a problem", str(err_count) + " files did not transfer :("
            )

    def clk_btn_reboot(self):
        # Send reboot command to HyperDecks
        tn = telnetlib.Telnet()

        try:
            tn.open(self.table.selectedIndexes()[0].data(), self.port)
            tn.write(b"reboot\n")
            tn.close()
        except Exception:
            pass

    def save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Save Files in Folder")
        return folder

    def refresh_table(self):
        self.table.unpopulate()
        inp = []
        for ii in range(len(self.prefs["deck_ips"])):
            inp.append(
                [
                    self.prefs["deck_ips"][ii],
                    str(self.prefs["save_folder"]),
                    str(self.prefs["transferred"][ii]),
                ]
            )

        self.table.populate(inp)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def update_prefs(self):
        if self.table.data()[0][1] == str(None):
            new_prefs = {
                "deck_ips": [],
                "save_folder": None,
                "transferred": [],
            }
        else:
            new_prefs = {
                "deck_ips": [],
                "save_folder": self.table.data()[0][1],
                "transferred": [],
            }
        for ip in self.table.data():
            new_prefs["deck_ips"].append(ip[0])
            new_prefs["transferred"].append(ip[2] == "True")

        self.prefs = new_prefs
        self.save_prefs()

    def save_prefs(self):
        prefs_file = open("prefs.pkl", "wb")
        pickle.dump(self.prefs, prefs_file)

    def open_prefs(self):
        prefs_file = open("prefs.pkl", "rb")
        self.prefs = pickle.load(prefs_file)


class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionBehavior(
            self.SelectionBehavior.SelectRows
        )  # Select whole rows

        self.setSelectionMode(
            self.SelectionMode.SingleSelection
        )  # Only select one row each time

        model = QStandardItemModel()
        self.setModel(model)

    def populate(self, data_in=None):
        if data_in is None:
            data_in = []
        model = self.model()
        for ii in range(len(data_in)):
            data = []
            if type(data_in[ii]) is list:
                for jj in range(len(data_in[ii])):
                    item = QStandardItem(data_in[ii][jj])
                    item.setDropEnabled(False)
                    data.append(item)
            else:
                item = QStandardItem(data_in[ii])
                item.setDropEnabled(False)
                data.append(item)
            model.insertRow(model.rowCount(), data)

    def unpopulate(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def rm_row(self):
        if self.model().rowCount() > 1:
            self.model().removeRow(self.currentIndex().row())
        else:
            print("Cannot delete only IP address")

    def data(self):
        model = self.model()
        data = []
        for ii in range(model.rowCount()):
            data.append([])
            for jj in range(model.columnCount()):
                index = model.index(ii, jj)
                data[ii].append(model.data(index))

        return data


def valid_ip_address(sample_str):
    """Returns True if given string is a
    valid IP Address, else returns False"""
    result = True
    match_obj = re.search(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", sample_str)
    if match_obj is None:
        result = False
    else:
        for value in match_obj.groups():
            if int(value) > 255:
                result = False
                break
    return result


def run():
    from sys import exit as SysExit

    app = QApplication([])
    ex = App()
    ex.show()
    SysExit(app.exec())


if __name__ == "__main__":
    run()
