class Logger:
    """Simple logging utility for consistency."""

    @staticmethod
    def info(msg: str):
        print(f"[INFO] {msg}")

    @staticmethod
    def success(msg: str):
        print(f"[SUCCESS] {msg}")

    @staticmethod
    def error(msg: str):
        print(f"[ERROR] {msg}")
