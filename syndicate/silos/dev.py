from syndicate.utils import action_log_group, action_log

@action_log_group("dev")
def do_the_thing(api_key):
    action_log("Hello? Yes, this is DEV.")
    return True
