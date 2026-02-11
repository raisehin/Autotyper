# AutoTyper Lite

A lightweight, efficient automated typing utility built with Python and Tkinter. Designed for speed, ease of use, and a premium feel.

Wallahi no virus 

### Prerequisites
- Python 3.x
- Dependencies listed in `requirements.txt`

  Stuff you ought to know before using it: 

  I think google docs and sites tracks your wpm, idk how well jitter works but be weary when using the auto typer

  made cuz heads was charging for a auto typer for no reason

  
### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/raisehin/Autotyper.git
   cd autotyper-lite
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python source/autotyper_tk.py
   ```

## Creating the Executable
To bundle the application into a standalone `.exe`:
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "source/hobgoblin_tech-paper-7098789_1920.png;." --icon "source/hobgoblin_tech-paper-7098789_1920.png" source/autotyper_tk.py
```

## License
MIT License - see [LICENSE](LICENSE) for details.
