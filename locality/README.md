### Install and usage
- Get the release from [here](https://github.com/classroom-dee/miniapps/releases/latest)
- Unzip
- Use with right-click context menu

### Dev
**If you have an older version, you need to delete the config file under c:/users/your-user-name/.locale_master.json**
1. `pip install -r requirements.txt --no-cache-dir`
2. `python main.py`

### Build
1. Clone this, make a disposable env `python -m venv .venv` and then `source .venv/bin/activate` or `.venv\Scripts\activate.bat` in Windows
2. `pip install pyinstaller`
3. `cd locality`
4. `pyinstaller --onefile --add-data="assets/meteocon/*.png:assets/meteocon" -n locale-master main.py`

### Simple Widget For Locality
- Weather
- DateTime
- City + Country
- Built with pyinstaller
- More importantly... no data collection!

### Icons
Weather icons are from [**Meteocons** by Bas Milius](https://github.com/basmilius/weather-icons)