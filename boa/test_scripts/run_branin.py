import datetime as dt
import logging
import shutil
import tempfile
import time
from pathlib import Path
from pprint import pformat

import click
from ax.service.utils.report_utils import exp_to_df

try:
    from wrappers import Wrapper
except ImportError:
    from .wrappers import Wrapper

from boa import (
    WrappedJobRunner,
    get_experiment,
    get_scheduler,
    load_yaml,
    make_experiment_dir,
)


@click.command()
@click.option("-o", "--output_dir", type=click.Path(), default="")
def main(output_dir):
    if output_dir:
        return run_opt(output_dir)
    with tempfile.TemporaryDirectory() as output_dir:
        return run_opt(output_dir)


def run_opt(output_dir):
    config_file = Path(__file__).parent / "synth_func_config.yaml"
    start = time.time()
    wrapper = Wrapper()
    config = wrapper.load_config(config_path=config_file, working_dir=output_dir)
    experiment_dir = wrapper.experiment_dir
    # Copy the experiment config to the experiment directory
    shutil.copyfile(config_file, experiment_dir / Path(config_file).name)
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
        filename=Path(experiment_dir) / "optimization.log",
        filemode="w",
        format=log_format,
        level=logging.DEBUG,
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logger = logging.getLogger(__file__)
    logger.info("Start time: %s", dt.datetime.now().strftime("%Y%m%dT%H%M%S"))

    experiment = get_experiment(config, WrappedJobRunner(wrapper=wrapper), wrapper)
    scheduler = get_scheduler(experiment, config=config)
    scheduler.run_all_trials()
    logger.info(pformat(scheduler.get_best_trial()))
    logger.info(scheduler.experiment.fetch_data().df)
    logging.info(pformat(scheduler.get_best_trial()))
    logging.info(scheduler.experiment.fetch_data().df)
    logging.info(exp_to_df(scheduler.experiment))

    logger.info("\nTrials completed! Total run time: %d", time.time() - start)
    return scheduler, config


if __name__ == "__main__":
    main()
