from attrs import define, validators, field
from pathlib import Path
from mcsas3 import McHat
from mcsas3 import McData1D  # , McData2D

# from mcsas3.mcmodelhistogrammer import McModelHistogrammer
# from mcsas3.mcanalysis import McAnalysis
import yaml
import argparse

# import logging
import multiprocessing
import sys  # , os
from sys import platform


@define
class McSAS3_cli_opt:
    """Runs the McSAS optimizer from the command line arguments"""

    def checkConfig(self, attribute, value):
        assert value.exists(), f"configuration file {value} must exist"
        assert (
            value.suffix == ".yaml"
        ), "configuration file must be a yaml file (and end in .yaml)"

    dataFile: Path = field(kw_only=True, validator=validators.instance_of(Path))
    resultFile: Path = field(kw_only=True, validator=validators.instance_of(Path))
    readConfigFile: Path = field(
        kw_only=True, validator=[validators.instance_of(Path), checkConfig]
    )
    runConfigFile: Path = field(
        kw_only=True, validator=[validators.instance_of(Path), checkConfig]
    )
    resultIndex: int = field(kw_only=True, validator=[validators.instance_of(int)])
    deleteIfExists: bool = field(kw_only=True, validator=[validators.instance_of(bool)])

    @dataFile.validator
    def fileExists(self, attribute, value):
        assert value.exists(), f"input data file {value} must exist"

    # init is auto-generated by attrs!!!

    def run(self):
        # remove any prior results file:
        if self.resultFile.is_file():
            # only remove result file if it is not the main file! This way, you can add McSAS to an existing nexus file
            if (self.resultFile != self.dataFile) & (self.deleteIfExists):
                self.resultFile.unlink()
        # read the configuration file
        with open(self.readConfigFile, "r") as f:
            readDict = yaml.safe_load(f)
        # load the data
        mds = McData1D.McData1D(
            filename=self.dataFile, resultIndex=self.resultIndex, **readDict
        )
        # store the full data in the result file:
        mds.store(self.resultFile)
        # read the configuration file
        with open(self.runConfigFile, "r") as f:
            optDict = yaml.safe_load(f)
        # run the Monte Carlo method
        mh = McHat.McHat(seed=None, resultIndex=self.resultIndex, **optDict)
        md = mds.measData.copy()
        mh.run(md, self.resultFile, resultIndex=self.resultIndex)


# adapted from: https://stackoverflow.com/questions/8220108/how-do-i-check-the-operating-system-in-python
def isLinux():
    return platform == "linux" or platform == "linux2"


def isMac():
    return platform == "darwin"


def isWindows():
    return platform == "win32"


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # manager=pyplot.get_current_fig_manager()
    # print manager
    # process input arguments
    parser = argparse.ArgumentParser(
        description="""
            Runs a McSAS optimization from the command line. 
            For this to work, you need to have YAML-formatted configuration files ready, 
            both for the input file read parameters, as well as for the optimization set-up. 

            After the McSAS run has completed, you can run the histogrammer (also from the command line)
            in the same way by feeding it the McSAS output file and a histogramming configuration file.

            Examples of these configuration files are provided in the example_configurations subdirectory. 

            Released under a GPLv3+ license.
            """
    )
    # TODO: add info about output files to be created ...
    parser.add_argument(
        "-f",
        "--dataFile",
        type=lambda p: Path(p).absolute(),
        default=Path(__file__).absolute().parent / "testdata" / "quickstartdemo1.csv",
        help="Path to the filename with the SAXS data",
        # required=True,
    )
    parser.add_argument(
        "-F",
        "--readConfigFile",
        type=lambda p: Path(p).absolute(),
        default=Path(__file__).absolute().parent
        / "example_configurations"
        / "read_config_csv.yaml",
        help="Path to the filename with the SAXS data",
        # required=True,
    )
    parser.add_argument(
        "-r",
        "--resultFile",
        type=lambda p: Path(p).absolute(),
        default=Path(__file__).absolute().parent / "test.nxs",
        help="Path to the file to create and store the McSAS3 result in",
        # required=True,
    )
    parser.add_argument(
        "-R",
        "--runConfigFile",
        type=lambda p: Path(p).absolute(),
        default=Path(__file__).absolute().parent
        / "example_configurations"
        / "run_config_spheres_auto.yaml",
        help="Path to the filename with the SAXS data",
        # required=True,
    )
    parser.add_argument(
        "-i",
        "--resultIndex",
        type=int,
        default=1,
        help="The result index to work on, in case you want multiple McSAS runs on the same data",
        # required=True,
    )
    parser.add_argument(
        "-d",
        "--deleteIfExists",
        # type=bool,
        # default=False,
        action="store_true",
        help="Delete the output file if it exists. This will need to be activated if you are overwriting previous optimizations ",
        # required=True,
    )
    if isMac():
        # on OSX remove automatically provided PID,
        # otherwise argparse exits and the bundle start fails silently
        for i in range(len(sys.argv)):
            if sys.argv[i].startswith("-psn"):  # PID provided by osx
                del sys.argv[i]
    try:
        args = parser.parse_args()
    except SystemExit:
        raise
    # initiate logging (to console stderr for now)
    # replaceStdOutErr() # replace all text output with our sinks

    adict = vars(args)
    m = McSAS3_cli_opt(**adict)
    m.run()
