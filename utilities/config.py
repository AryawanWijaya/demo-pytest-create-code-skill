from dataclasses import dataclass
from idlelib.editor import keynames
from pathlib import Path

from dotenv import dotenv_values

CONFIG_FILE=Path("config.properties")

def _load_properties(config_file=CONFIG_FILE):
    if not config_file.exists():
        raise FileNotFoundError(f"File not found: {config_file}")
    return dotenv_values(config_file) #python lib for read key=value file return dictionary

def _get(properties,key):
    if key not in properties:
        raise KeyError(f"Key not found: {key} missing on config.properties")
    return properties[key]

@dataclass
class Settings:
    base_url: str
    browser:str
    headless:bool
    default_timeout:int
    valid_username:str
    valid_password:str
    invalid_password:str
    invalid_username:str
    login_url_path:str
    secure_url_path:str
    config_values:dict

    def resolve_value(self,value):
        key=str(value)
        return self.config_values.get(key.strip().lower(),value)

    def url_path_for(self, page_name):
        key=f"{page_name}_url_path"
        attr=getattr(self,key,None)
        if attr is None:
            raise KeyError(f"url path not found: {key} on config.properties")
        return attr

    @classmethod
    def from_source(cls,browser=None,headless=None,base_url=None,config_file=CONFIG_FILE):
        properties=_load_properties(config_file)
        return cls(
            base_url=base_url or _get(properties,"base_url"),
            browser=browser or _get(properties,"browser"),
            headless=headless
            if headless is not None else
                _get(properties,"headless")=="true",
            default_timeout=int(_get(properties,"default_timeout")),
            valid_username=_get(properties,"valid_username"),
            valid_password=_get(properties,"valid_password"),
            invalid_password=_get(properties,"invalid_password"),
            invalid_username=_get(properties,"invalid_username"),
            login_url_path=_get(properties,"login_url_path"),
            secure_url_path=_get(properties,"secure_url_path"),
            config_values=properties,
        )