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
    def __init__(self, id, filename, device, data):
        threading.Thread.__init__(self, name=id, target=self.job)
        self.id = id
        self.filename = filename
        self.device = device
        self.name = device
        self.data = data

    def job(self):
        size = os.stat(self.filename).st_size
        cmd = ["dd", "bs=1048576", "if=%s" % self.filename, "of=%s" % self.device]
        dd = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        while dd.poll() is None:
            time.sleep(1)
            dd.send_signal(signal.SIGINFO)
            while True:
                l = dd.stderr.readline()
                if 'bytes transferred' in l:
                    self.data[self.id] = int(float(l.partition(' ')[0])*100/size)
                    break


class Monitor(threading.Thread):
    def __init__(self, name, threads, pbar, data):
        threading.Thread.__init__(self, name=name, target=self.job)
        self.threads = threads
        self.pbar = pbar
        self.data = data

    def job(self):
        while True:
            time.sleep(1)
            all_jobs_done = True
            for t in self.threads:
                if t.is_alive():
                    all_jobs_done = False
                else:
                    self.pbar[t.id].finish()
            for t in self.threads:
                self.pbar[t.id].update(self.data[t.id])
            if all_jobs_done:
                break


def run(input):
    term = blessed.Terminal()

    data = {}
    writers = {}
    pbar = {}

    jobs = []
    i = 0
    for device in input['devices']:
        jobs.append(DDJob("job-%s" % i, input['file'], device, data))
        i = i + 1

    i = 2
    for t in jobs:
        data[t.id] = 0
        t.start()
        writers[t.id] = Writer(term, (1, i), t.id)
        pbar[t.id] = ProgressBar(fd=writers[t.id],
                                 widgets=[Percentage(), ' ',
                                          FormatLabel(t.name), ' ',
                                          Bar('='), ' ',
                                          FileTransferSpeed(unit="M"), ' - ', ETA()])
        pbar[t.id].start()
        pbar[t.id].update(0)
        i = i + 1

    with term.fullscreen():
        with term.location(0, 0):
            print "%s RuggedPOD Firmware %s" % ("=" * 30, "=" * 30)

        monitor = Monitor("ddmonitor", jobs, pbar, data)
        monitor.start()
        monitor.join()
        raw_input("")
