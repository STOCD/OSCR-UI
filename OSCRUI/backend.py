"""Backend inteface to the OSCR web server"""

import tempfile

import OSCR_django_client
from OSCR.utilities import logline_to_str
from OSCR_django_client.api import CombatlogApi
from PyQt6.QtWidgets import QMessageBox


def upload_callback(self):
    """
    Helper function to grab the current combat and upload it to the backend.
    """

    with tempfile.NamedTemporaryFile() as file:
        for line in self.parser1.active_combat.log_data:
            file.write(logline_to_str(line).encode())
            file.flush()
        self.backend.upload(file.name)


class OSCRClient:
    def __init__(self, address=None):
        """Initialize an instance of the OSCR backlend client"""

        # TODO: This is a test domain and not for production.
        if not address:
            # self.address = "https://kraust-oscr.koyeb.app/"
            self.address = "http://127.0.0.1:8000"

        self.api_client = OSCR_django_client.api_client.ApiClient()
        self.api_client.configuration.host = self.address
        self.api_combatlog = CombatlogApi(api_client=self.api_client)

    def upload(self, filename):
        """Upload a combat log located at path for analysis"""

        reply = QMessageBox()
        reply.setWindowTitle("Open Source Combatlog Reader")

        try:
            print(filename)
            res = self.api_combatlog.combatlog_upload(file=filename)
            lines = []
            for entry in res:
                lines.append(entry.detail)
            reply.setText("\n".join(lines))
        except OSCR_django_client.exceptions.ServiceException as e:
            reply.setText(e)

        reply.exec()
