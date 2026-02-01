from ui import Widget
from config import load_config


def main():
    cfg = load_config()
    app = Widget(cfg)
    app.title("WorldClock+Weather")
    # drop shadow-like border
    app.configure(highlightthickness=1, highlightbackground="#333333")
    app.mainloop()


if __name__ == "__main__":
    main()
