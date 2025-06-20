from utils.logger import get_logger

logger = get_logger("command_runner")


def run_command(conn, command):
    logger.info(f"Running command: {command}")
    # TODO: Implement actual remote command execution using conn
    # result = conn.exec_command(command)
    result = f"Simulated output for: {command}"
    logger.info(f"Result: {result}")
    return result


def run_commands(conn, commands):
    results = []
    for cmd in commands:
        logger.info(f"Running command: {cmd}")
        # result = conn.exec_command(cmd)
        result = f"Simulated output for: {cmd}"
        logger.info(f"Result: {result}")
        results.append(result)
    return results
