import os

class CFGLoader:

    @staticmethod
    def get_project_root() -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_cfg_env_path():
        cfg_env_path = os.path.join(CFGLoader.get_project_root(), "cfg/cfg.env")
        return cfg_env_path