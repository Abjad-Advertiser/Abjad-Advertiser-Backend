from user_agents import parse


def get_device_type(user_agent_string: str) -> str:
    parsed_user_agent = parse(user_agent_string)
    if parsed_user_agent.is_mobile or parsed_user_agent.is_touch_capable:
        return "mobile"
    elif parsed_user_agent.is_tablet:
        return "tablet"
    elif parsed_user_agent.is_pc:
        return "desktop"
    else:
        # Don't register any uknown devices as this may lead to false positives
        raise ValueError("Unknown device type")
