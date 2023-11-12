import logging

def format_text_left(text: str, width: int) -> str:
    difference = width - len(text)
    if difference < 0:
        text = text[:width]
    
    return text + " " * difference

class LoggingFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\x1b[38;5;240;1m",  # gray + bold
        logging.INFO: "\x1b[34;1m",  # blue + bold
        logging.WARNING: "\x1b[33;1m",  # yellow + bold
        logging.ERROR: "\x1b[31m",  # red
        logging.CRITICAL: "\x1b[31;1m",  # red + bold
    }

    FORMAT = (
        "{black}{asctime}{reset} {levelcolor}{levelname:<8}{reset} {green}{name}{reset} {message}"
    )

    def format(self, record):
        # get the color corresponding to the log level
        log_color = self.COLORS.get(record.levelno, "")

        # apply the color and formatting
        format_str = self.FORMAT.replace("{black}", "\x1b[30;1m").replace("{reset}", "\x1b[0m")
        format_str = format_str.replace("{levelcolor}", log_color).replace("{green}", "\x1b[32;1m")

        # create a formatter with 'format_str'
        formatter = logging.Formatter(format_str, "%Y-%m-%d %H:%M:%S", style="{")
        
        # return the result
        return formatter.format(record)

class logger(logging.Logger):
    def __init__(self, name="discord_bot", log_file="discord.log"):
        super().__init__(name)
        self.setLevel(logging.INFO)

        # Create handlers that will output logs to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(LoggingFormatter())

        # Create handlers that will save logs to a file
        file_handler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
        file_handler_formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
        )
        file_handler.setFormatter(file_handler_formatter)

        # Add the handlers to the logger
        self.addHandler(console_handler)
        self.addHandler(file_handler)