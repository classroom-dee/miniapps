### Simple Widget For Locality
- Weather
- DateTime
- City + Country
- Built with pyinstaller
- More importantly... no data collection!

### Install and usage
**If you have an older version, you need to delete the config file under c:/users/your-user-name/.locale_master.json**
- Get the release from [here](https://github.com/classroom-dee/miniapps/releases/latest)
- Unzip
- Use with right-click context menu
- Don't add/remove things too quickly -> will quickly hit the API rate limit

### Dev
1. `pip install -r requirements.txt --no-cache-dir`
2. `python main.py`

### Build
**In windows, your Python must be built with Tcl/Tk, i.e., Python from the MS Store**
**For Linux, install python with python3-tk(Debian) -> Desktop versions seem to include this**
1. Clone this, make a disposable env `python -m venv .venv` and then `source .venv/bin/activate` or `.venv\Scripts\activate.bat` in Windows
2. `pip install pyinstaller`
3. `cd locality`
4. `pyinstaller --onefile --add-data="assets/meteocon/*.png:assets/meteocon" --hidden-import=requests -n locale-master main.py`
5. Or, on Windows: `pyinstaller.exe --onefile --add-data="assets/meteocon:assets/meteocon" --hidden-import=requests --no-console -n locale-master-win main.py`

### Todos and issues
- Build for Linux

### Acknowledgement
Weather icons from [**Meteocons** by Bas Milius](https://github.com/basmilius/weather-icons)