from datetime import datetime
import paramiko
import keyring
import csv


class DataFile:
    """Class for the csv run data files to simplify usage."""

    def __init__(self, save_folder_path, tag):
        self.filename = "{}/{}-{}.csv".format(
            save_folder_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), tag
        )
        self.remote_path = "/home/ucn/online/gradiometer/run_data/{}-{}.csv".format(
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), tag
        )
        self.fieldnames = [
            "timestamp",
            "time",
            "position",
            "x1",
            "y1",
            "z1",
            "x2",
            "y2",
            "z2",
            "dx1",
            "dy1",
            "dz1",
            "dx2",
            "dy2",
            "dz2",
        ]
        self.csvfile = open(self.filename, "w")
        self.writer = csv.DictWriter(self.csvfile, self.fieldnames)
        self.writer.writeheader()

    def write_row(self, values):
        row_dict = dict(zip(self.fieldnames, values))
        for key, value in row_dict.items():
            self.writer.writerow([key, value])

    def upload_to_server(self):
        host = "daq01.ucn.triumf.ca"
        port = 22

        service_name = "daq01"
        username = "ucn"
        # set the server password in terminal before this
        password = keyring.get_password(service_name, username)
        if password is None:
            err = (
                "Server password has not been set with keyring. Type the following into the "
                'terminal:\n>python3\n>import keyring\n>keyring.set_password("daq01", "ucn", "the_password") '
            )
            raise NameError(err)
        else:

            t = paramiko.Transport((host, port))
            t.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.put(self.filename, self.remote_path)
            try:
                sftp.stat(self.remote_path)
                print("Run data file successfully uploaded to server.")
            except IOError:
                print("There was a problem uploading the run data file to the server.")

            sftp.close()
            t.close()

    def close(self):
        self.csvfile.close()
