# Trading Dashboard

A modern, dark-themed dashboard for monitoring cryptocurrency trading activities using Flask, MySQL, and Bybit API.

## Features

- Real-time trading data visualization
- Performance tracking for multiple cryptocurrencies (BTC, ETH, SOL)
- Detailed trade history and statistics
- Decision event monitoring
- Database explorer with filtering capabilities
- Responsive design with dark theme

## Screenshots

(Add screenshots when available)

## Requirements

- Python 3.8+
- MySQL 8.0+
- Bybit API access (for account balance)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/trading-dashboard.git
cd trading-dashboard
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Configure the database and API settings:

Edit the files in the `config` directory:
- `db_config.json`: Database connection details
- `api_config.json`: Bybit API credentials for each cryptocurrency

5. Run the application:

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000/

## Configuration

### Database Configuration

Edit `config/db_config.json` with your MySQL database details:

```json
{
    "host": "your-database-host",
    "user": "your-database-user",
    "password": "your-database-password",
    "database": "trading_system",
    "port": 3306
}
```

### API Configuration

Edit `config/api_config.json` with your Bybit API credentials:

```json
{
    "bybit_api": {
        "BTC": {
            "key": "your-btc-api-key",
            "secret": "your-btc-api-secret"
        },
        "ETH": {
            "key": "your-eth-api-key",
            "secret": "your-eth-api-secret"
        },
        "SOL": {
            "key": "your-sol-api-key",
            "secret": "your-sol-api-secret"
        }
    }
}
```

## Project Structure

```
/trading-dashboard
    /static
        /css
            custom.css
        /js
            charts.js
            dashboard.js
        /img
            logo.png
    /templates
        base.html
        index.html
        settings.html
        data.html
        symbol_detail.html
    /config
        api_config.json
        db_config.json
    app.py
    bybit_client.py
    db_manager.py
    utils.py
    requirements.txt
    README.md
    .gitignore
```

## Database Schema

The application uses the following database tables:

1. `trades`: Records of individual trades
2. `decision_events`: Trading decision events (open/close positions)
3. `execution_events`: Execution results of trading decisions

## Deployment

### Using Gunicorn (Linux/macOS)

1. Install Gunicorn:

```bash
pip install gunicorn
```

2. Run with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using Waitress (Windows)

1. Install Waitress:

```bash
pip install waitress
```

2. Run with Waitress:

```bash
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
