from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

from app.core.controller import ApplicationController
from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Serial Joystick Keymapper")
    app.setOrganizationName("OpenProject")
    app.setQuitOnLastWindowClosed(False)

    app_root = Path(__file__).resolve().parent
    profiles_dir = app_root / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    controller = ApplicationController(profiles_dir=profiles_dir)
    window = MainWindow(controller=controller)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
