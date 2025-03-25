try:
    from get_token_path_temp import *
    # directry path
    dir_path = get_dir_path()

    # IBM Quantum API token and information for your hub
    IBM_token = get_token()
    hub, group, project = get_hub_group_project()

except ImportError:

    # directry path
    dir_path = "/xxxx/Random_algorithm_dynamic_circuit_open/save/" 

    # IBM Quantum API token and information for your hub
    IBM_token = "xxxx"
    hub = "xxxx"
    group = "xxxx"
    project = "xxxx"

    def get_dir_path():
        return dir_path

    def get_token():
        return IBM_token

    def get_hub_group_project():
        return hub, group, project


