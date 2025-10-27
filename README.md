# Neural Bloom — Desktop

## Run (dev)
```bash
python -m venv .venv
. .venv/Scripts/activate   # on Windows
pip install -r requirements.txt
python main.py
```

## Build Windows .exe
```bash
pip install pyinstaller
pyinstaller --noconfirm \
  --name "Neural Bloom" \
  --windowed \
  --icon app/assets/logo.ico \
  main.py
```
> Tip: از SVG لوگو می‌تونی با ابزارهایی مثل Inkscape خروجی `.ico` بگیری.

## Online Leaderboard (optional)
Provide an `API_URL` in `app/settings.py` pointing to an endpoint supporting:
- `POST /leaderboard { name, score, mode }`
- `GET  /leaderboard?mode=<endless|story>&limit=10`
```

---

### نکات نهایی
- UI تماماً دکمه/کنترل استاندارد Qt هست (شروع، توقف، ریست، انتخاب حالت، تغییر تم، موزیک، SFX).
- ساختار فولدرها «تمیز» و قابل گسترش است. اگر بخواهی، بخش موسیقی را با `QMediaPlayer` و فایل‌های صوتی سفارشی تکمیل می‌کنم.
- اگر یکی از **نام‌های برند** مورد پسندت بود، می‌تونم فوراً لوگوی نهایی (SVG + PNG + ICO) و فایل‌های PyInstaller آماده‌شده با آیکن اختصاصی را برات بسازم.
