from kitstructlog import InitLoggers, LoggerReg

from src.config.configuration import Configuration


class Loggers(InitLoggers):
    main = LoggerReg(name="MAIN", level=LoggerReg.Level.DEBUG)
    logging_middleware = LoggerReg(name="LOGGING", level=LoggerReg.Level.INFO)


__all__ = ["Configuration", "Loggers"]
