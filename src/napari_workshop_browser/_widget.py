import sys
import os
import appdirs
import zipfile
import requests
from typing import TYPE_CHECKING

from qtpy.QtWidgets import (
    QPushButton,
    QWidget,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QVBoxLayout,
    QLabel,
)

from superqt import ensure_main_thread
from superqt.utils import thread_worker

if TYPE_CHECKING:
    import napari

# Global list of URLs
URL_LIST = [
    "https://github.com/napari/napari-workshop-template/archive/refs/heads/main.zip",
    "https://github.com/kephale/napari-dl-at-mbl-2024/archive/refs/heads/main.zip",
    "https://github.com/kephale/napari-workshop-halfway-to-i2k/archive/refs/heads/main.zip",    
    "https://github.com/kephale/napari-workshop-mandm-2023/archive/refs/heads/main.zip",
]

def in_notebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type of shell
    except NameError:
        return False  # Not running in an IPython shell


def download_file(url, save_path):
    response = requests.get(url)
    with open(save_path, "wb") as file:
        file.write(response.content)


def unzip_file(file_path, extract_dir):
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)


def download_and_unzip(url):
    # Get the cache directory path using appdirs
    cache_dir = appdirs.user_cache_dir()
    print(f"Cache directory: {cache_dir}")

    # Create a temporary directory inside the cache directory
    temp_dir = os.path.join(cache_dir, "temp_unzip")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Temporary directory: {temp_dir}")

    try:
        # Download the zip file
        zip_file_path = os.path.join(temp_dir, "downloaded_file.zip")

        # Check if this is a URL, if so download
        if url.startswith("https"):
            download_file(url, zip_file_path)
            print("File successfully downloaded.")
        else:
            # Otherwise we assume the URL is a local zip path
            zip_file_path = url

        # Extract the zip file
        unzip_file(zip_file_path, temp_dir)
        print("File successfully unzipped.")

        return temp_dir

    except Exception as e:
        print(f"Error: {e}")

    return None


def cleanup_temp_directory(temp_dir):
    # Clean up the temporary directory
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)
        print("Temporary directory deleted.")


class WorkshopWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.url_combobox = QComboBox(self)
        self.url_combobox.setEditable(True)
        self.url_combobox.addItems(URL_LIST)
        self.url_combobox.setCurrentIndex(0)

        self.napari_workshop_template = QComboBox(self)
        self.napari_workshop_template.addItems(["Latest", "None"])

        btn = QPushButton("Launch Workshop")
        btn.clicked.connect(self._on_click)

        # Layout
        self.setLayout(QVBoxLayout())

        label = QLabel(self)
        label.setText("Workshop zip URL")
        self.layout().addWidget(label)
        self.layout().addWidget(self.url_combobox)

        label = QLabel(self)
        label.setText("Workshop version")
        self.layout().addWidget(label)
        self.layout().addWidget(self.napari_workshop_template)

        self.layout().addWidget(btn)

    def _on_click(self):
        self.run()

    def run(self):
        # Hide the original window. This is really wasteful.
        self.viewer.window._qt_window.hide()

        try:
            from jupyter_server.serverapp import ServerApp as NotebookApp
        except ImportError:
            from notebook.notebookapp import NotebookApp

        @thread_worker
        @ensure_main_thread
        def launch_jupyter_notebook():
            try:
                if in_notebook():
                    print("Already running within a Jupyter environment.")
                    return

                # Get the workshop URL and unzip it
                workshop_zip_url = self.url_combobox.currentText()
                notebook_dir = download_and_unzip(workshop_zip_url)

                # If 'Latest' is selected, adjust the directory
                if self.napari_workshop_template.currentText() == "Latest":
                    repo_archives = [
                        name
                        for name in os.listdir(notebook_dir)
                        if os.path.isdir(os.path.join(notebook_dir, name))
                        and name.endswith("-main")
                    ]
                    notebook_dir = os.path.join(
                        notebook_dir,
                        repo_archives[0],
                        "napari-workshops",
                        "notebooks",
                    )
                    print(f"Notebook dir is {notebook_dir}")

                # Start the Jupyter Notebook server
                app = NotebookApp.instance()
                app.open_browser = True
                app.notebook_dir = notebook_dir

                os.chdir(notebook_dir)

                app.initialize()
                app.start()

                print("Jupyter Notebook has been launched successfully.")

            except Exception as e:
                print(
                    "An error occurred while launching Jupyter Notebook:",
                    str(e),
                )

        worker = launch_jupyter_notebook()

        def restore_napari():
            self.viewer.window._qt_window.show()

        worker.finished.connect(restore_napari)

        worker.start()


if __name__ == "__main__":
    import napari

    viewer = napari.Viewer()

    widget = WorkshopWidget(viewer)

    viewer.window.add_dock_widget(widget)
