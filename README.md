# Server Dashboard

A lightweight desktop app to monitor and control your local servers (XAMPP, Apache, MySQL, PostgreSQL, MongoDB, Redis) with a simple GUI.

## Requirements

- Python 3
- PyQt5

```bash
sudo apt install python3 python3-pip
pip3 install PyQt5
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Maik4-0/serverdash.git
cd serverdash
```

2. Run the app:

```bash
python3 app/main.py
```

## Usage

- **Green dot** = service is running
- **Red dot** = service is stopped
- Click a section header to **collapse or expand** it
- Use the **Start / Stop** buttons to control each service
- The app minimizes to the **system tray** when closed — right-click the tray icon to quit

## Customizing Colors

Edit `app/config.json` to change the color scheme:

```json
{
  "colors": {
    "bg":      "#1e2a1f",
    "surface": "#243325",
    "border":  "#346739",
    "accent":  "#79AE6F",
    "light":   "#9FCB98",
    "text":    "#F2EDC2",
    "subtext": "#79AE6F",
    "red":     "#c0614a"
  }
}
```

Restart the app after saving for changes to apply.

## Adding Services Without Password Prompts

Create a sudoers rule so the app can start/stop services without asking for your password:

```bash
sudo visudo -f /etc/sudoers.d/serverdash
```

Add:

```
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/bin/systemctl start apache2, /usr/bin/systemctl stop apache2, /usr/bin/systemctl start mysql, /usr/bin/systemctl stop mysql, /opt/lampp/bin/apachectl, /opt/lampp/lampp
```
