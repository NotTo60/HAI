from utils.logger import get_logger

logger = get_logger("command_runner")


def run_command(conn, command):
    logger.info(f"Running command: {command}")
    result = conn.exec_command(command)
    # Ensure result is always a tuple (out, err)
    if isinstance(result, tuple) and len(result) == 2:
        out, err = result
    else:
        out, err = result, ""
    logger.info(f"Result: {out}")
    return out, err


def run_commands(conn, commands):
    results = []
    for cmd in commands:
        logger.info(f"Running command: {cmd}")
        out, err = conn.exec_command(cmd)
        logger.info(f"Result: {out}")
        results.append((out, err))
    return results
