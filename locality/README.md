# Locality Widget

A lightweight desktop widget that displays local information such as weather, date/time, and location. Built with Python and packaged for easy use, with a focus on privacy and simplicity.

### What it does
- Displays current weather
- Shows date and time
- Displays city and country
- Runs as a small desktop widget
- Uses caching to avoid hitting rate limits
- Uses a right-click context menu for interaction

### Why
- Built as a minimal, local-first widget for quick glanceable information
- Focuses on privacy(no data collection) and simplicity
- Designed to be lightweight and unobtrusive

### Dependencies
- Tkinter must be bundled in your python. Check with `python -m "import tkinter"`
- `pyinstaller` for building
- See `requirements.txt`

### Setup
1. Download the latest release from: https://github.com/classroom-dee/miniapps/releases/latest
2. Unzip the archive
3. Run the executable
4. Use the right-click context menu to interact

*If you have an older version, delete the config file at: C:/Users/your-username/.locale_master.json*

*Avoid rapid interactions — you may hit API rate limits.*

### Run
- `python main.py`

### Screenshot
![Screenshot](./capgen.jpeg)

### Future Improvements
- Other os build support