import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

class CustomLogger:
    """
    Logger aziendale standardizzato.
    Include formattazione a colori per terminale e salvataggio su file rotativo.
    """
    
    # Codici colore ANSI per il terminale (Palette pastello/soft dove possibile)
    _COLORS = {
        'DEBUG': "\033[38;5;117m",    # Light blue
        'INFO': "\033[38;5;114m",     # Soft green
        'WARNING': "\033[38;5;222m",  # Soft yellow/peach
        'ERROR': "\033[38;5;167m",    # Soft red
        'CRITICAL': "\033[48;5;167;38;5;231m", # Red background, white text
        'RESET': "\033[0m"      # Reset
    }

    @staticmethod
    def get_logger(name: str = "AppLogger", log_file: str = "app.log", level=logging.DEBUG):
        """
        Ritorna un'istanza di logger configurata secondo lo standard.
        """
        logger = logging.getLogger(name)

        if logger.hasHandlers():
            return logger

        logger.setLevel(level)

        # 1. Formattazione per i log su file (nessun colore)
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s (%(filename)s:%(lineno)d)'
        )

        # 2. Handler per il Terminale (con colori pastello)
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                color = CustomLogger._COLORS.get(record.levelname, CustomLogger._COLORS['RESET'])
                reset = CustomLogger._COLORS['RESET']
                record.levelname = f"{color}{record.levelname}{reset}"
                return super().format(record)

        stream_format = ColorFormatter('%(asctime)s | %(levelname)s | %(message)s')
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(stream_format)
        logger.addHandler(stream_handler)

        # 3. Handler per il File (Rotativo)
        log_path = Path("logs")
        try:
            log_path.mkdir(exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path / log_file, 
                maxBytes=5*1024*1024, 
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback se non ci sono i permessi per creare la cartella logs
            stream_handler.stream.write(f"\\nImpossibile creare la cartella logs: {e}\\n")

        return logger

# Singleton per uso immediato
logger = CustomLogger.get_logger()