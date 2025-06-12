# Advanced Uninstaller

A modern application uninstaller with a beautiful UI built using CustomTkinter. This application helps you manage and uninstall programs installed on your Windows system, with additional cleanup features.

## Features

- Modern, dark-themed UI using CustomTkinter
- Lists all installed applications on your system
- Search functionality to quickly find applications
- One-click uninstallation
- Automatic cleanup of leftover files
- Progress tracking during uninstallation
- Threaded operations to keep the UI responsive

## Requirements

- Python 3.7 or higher
- Windows operating system
- Required Python packages (install using `pip install -r requirements.txt`):
  - customtkinter==5.2.1

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python uninstaller.py
   ```

2. The application will automatically load all installed programs
3. Use the search bar to filter applications
4. Click the "Uninstall" button next to any application to remove it
5. Confirm the uninstallation when prompted
6. The application will handle the uninstallation and cleanup process

## Note

This application requires administrative privileges to uninstall programs and clean up leftover files. Make sure to run it with appropriate permissions.

## License

This project is open source and available under the MIT License. 
