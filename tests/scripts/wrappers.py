import os
from pathlib import Path
import subprocess
import json

from ax import Trial
from ax.utils.measurement.synthetic_functions import hartmann6
import numpy as np

from optiwrap import BaseWrapper, make_trial_dir, get_trial_dir

class TestWrapper(BaseWrapper):
    _processes = []
    model_dir = Path(__file__).parent

    def __init__(self, ex_settings, experiment_dir):
        self.ex_settings = ex_settings
        self.experiment_dir = experiment_dir

    def run_model(self, trial: Trial):
        trial_dir = make_trial_dir(self.experiment_dir, trial.index).resolve()

        model_dir = self.ex_settings["model_dir"]

        os.chdir(model_dir)

        cmd = (f"python synth_func_cli.py --output_dir {trial_dir} --standard_dev {self.ex_settings['metric']['noise_sd']}"
               f" {' '.join(str(val) for val in trial.arm.parameters.values())}")

        args = cmd.split()
        popen = subprocess.Popen(
            args, stdout=subprocess.PIPE, universal_newlines=True
        )
        self._processes.append(popen)

    def set_trial_status(self, trial: Trial) -> None:
        """ "Get status of the job by a given ID. For simplicity of the example,
        return an Ax `TrialStatus`.
        """
        output_file = get_trial_dir(self.experiment_dir, trial.index) / "output.json"

        if output_file.exists():
            trial.mark_completed()

    def fetch_trial_data(self, trial: Trial, *args, **kwargs):
        output_file = get_trial_dir(self.experiment_dir, trial.index) / "output.json"
        with open(output_file, "r") as f:
            data = json.load(f)

        # return dict(a=data["output"])
        # return dict(y_true=[hartmann6.fmin], y_pred=[np.mean(data["output"])])
        return dict(y_true=np.full(10, hartmann6.fmin), y_pred=data["output"])


def exit_handler():
    for process in TestWrapper._processes:
        process.kill()