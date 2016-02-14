# RuggedPOD Tools
#
# Copyright (C) 2016 Guillaume Giamarchi <guillaume.guillaume@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import threading
import time
import signal
import os
import subprocess
import re

import blessed

from progressbar import ProgressBar
from progressbar.widgets import FormatLabel, Bar, Percentage, ETA, FileTransferSpeed, Timer


class Writer(object):
    def __init__(self, term, location, label):
        self.term = term
        self.location = location
        self.label = label

    def write(self, string):
        with self.term.location(*self.location):
            print(string)


class DDJob(threading.Thread):
    def __init__(self, id, filename, device, writer):
        threading.Thread.__init__(self, name=id, target=self.job)
        self.id = id
        self.filename = filename
        self.device = device
        self.name = device
        self.progress = ProgressBar(fd=writer,
                                    widgets=[Percentage(), ' ',
                                             FormatLabel(device), ' ',
                                             Bar('='), ' ',
                                             FileTransferSpeed(unit="M"), ' - ', ETA()])

    def job(self):
        self.progress.start()
        size = os.stat(self.filename).st_size
        cmd = ["dd", "bs=1048576", "if=%s" % self.filename, "of=%s" % self.device]
        dd = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        while dd.poll() is None:
            time.sleep(1)
            dd.send_signal(signal.SIGINFO)
            while True:
                l = dd.stderr.readline()
                if 'bytes transferred' in l:
                    self.progress.update(int(float(l.partition(' ')[0])*100/size))
                    break
        self.progress.finish()


class Monitor(threading.Thread):
    def __init__(self, name, term, file, jobs):
        threading.Thread.__init__(self, name=name, target=self.job)
        self.term = term
        self.jobs = jobs
        self.file = file
        self.finish = False

    def job(self):
        if self.jobs:
            for job in self.jobs:
                job.join()
            return

        devices = _read_devices("^disk[0-9]+$")
        i = 2

        while True:
            if self.finish:
                break
            time.sleep(.2)
            new_devices = _read_devices("^disk[0-9]+$")
            new, _ = _diff_arrays(new_devices, devices)
            if new:
                for device in new:
                    self.jobs.append(_start_job(i, self.term, self.file, "/dev/" + device))
                    i = i + 1
            devices = new_devices


def run(input):
    term = blessed.Terminal()

    with term.fullscreen():
        with term.location(0, 0):
            print "%s RuggedPOD Firmware %s" % ("=" * 30, "=" * 30)

        jobs = []
        if "devices" in input:
            i = 0
            for device in input["devices"]:
                jobs.append(_start_job(i, term, input['file'], device))
                i = i + 1

        monitor = Monitor("ddmonitor", term, input['file'], jobs)
        monitor.start()

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            print 'interrupted!'
            monitor.finish = True

        monitor.join()

    if "devices" in input:
        raw_input("")


def _start_job(i, term, file, device):
    job_id = "job-%s" % i
    job = DDJob(job_id, file, device, Writer(term, (1, i+2), job_id))
    job.start()
    return job


def _diff_arrays(new, old):
    """
    returns a couple (n, m) where n is an array containing
    elements present in new but not in old. And m is an
    array containing elements present in old but not present
    in new
    """
    return ([e for e in new if e not in set(old)], [e for e in old if e not in set(new)])


def _read_devices(pattern):
    pattern = re.compile(pattern)
    return [e for e in os.listdir("/dev") if pattern.match(e)]
