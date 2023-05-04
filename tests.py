from datetime import datetime
from json import load, dump

with open("data/config.json") as config:
    cfg = load(config)
    if "update_times" in cfg.keys() and cfg["update_keys"] is not None:
        pass
    # cfg["update_times"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # dump(cfg, config)