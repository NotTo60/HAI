from utils.logger import get_logger
from utils.constants import DEFAULT_TIMEOUT

logger = get_logger("command_runner")


def run_command(conn, command, timeout=DEFAULT_TIMEOUT):
    logger.info(f"Running command: {command}")
    try:
        result = conn.exec_command(command)
        # Ensure result is always a tuple (out, err)
        if isinstance(result, tuple) and len(result) == 2:
            out, err = result
        else:
            out, err = result, ""
        logger.info(f"Result: {out}")
        return out, err
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return "", str(e)


def run_commands(conn, commands, timeout=DEFAULT_TIMEOUT):
    results = []
    for cmd in commands:
        logger.info(f"Running command: {cmd}")
        try:
            out, err = conn.exec_command(cmd)
            logger.info(f"Result: {out}")
            results.append((out, err))
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            results.append(("", str(e)))
    return results
