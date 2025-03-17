import os
import yaml
from dotenv import load_dotenv

# Load environment variables from a .env file located in the same directory or project root.
load_dotenv()

def load_config(config_file="config/config.yaml"):
    """
    Loads the configuration from a YAML file and replaces placeholders
    with values from environment variables.
    
    Args:
        config_file (str): Path to the YAML configuration file.
        
    Returns:
        dict: A dictionary with configuration settings.
    """
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    def replace_env_vars(item):
        """
        Recursively replace any string of the form ${VAR_NAME} with the
        corresponding environment variable.
        """
        if isinstance(item, dict):
            return {k: replace_env_vars(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [replace_env_vars(elem) for elem in item]
        elif isinstance(item, str):
            # Replace all occurrences of ${VAR_NAME} with os.getenv("VAR_NAME")
            while "${" in item:
                start = item.find("${")
                end = item.find("}", start)
                if end == -1:
                    break
                var_name = item[start+2:end]
                var_value = os.getenv(var_name, "")
                item = item[:start] + var_value + item[end+1:]
            return item
        else:
            return item

    return replace_env_vars(config)

# Load configuration into a global variable for use across the application.
config = load_config()

if __name__ == "__main__":
    # For testing: print the loaded configuration.
    import pprint
    pprint.pprint(config)
