from pathlib import Path


ROOT = Path(__file__).parent.parent.parent


TECHNIQUES_PATH = ROOT.joinpath("techniques")
RESOURCES_PATH = ROOT.joinpath("resources")
MOCK_DATA_PATH = RESOURCES_PATH.joinpath("mock_data.yaml")
