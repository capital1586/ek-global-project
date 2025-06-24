# SmartScreener - Pakistan Stock Exchange (PSX) Screener

SmartScreener is a Django-based web application that provides a comprehensive stock screening tool for the Pakistan Stock Exchange (PSX). The application offers powerful filtering, sorting, and data visualization features to help investors make informed decisions.

## Features

- **Real-time Stock Data**: Fetches up-to-date stock information from the PSX API
- **Advanced Filtering**: Filter stocks by various criteria including:
  - Sector and Industry
  - Price Range
  - Change Percentage
  - Volume
  - Market Capitalization
  - P/E Ratio
- **Technical Analysis**: View technical indicators for individual stocks
- **Market Overview**: Real-time index values and market trends
- **Mock Data Fallback**: Automatically falls back to mock data if the API is unavailable

## Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- PostgreSQL (recommended) or SQLite

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smartscreener.git
   cd smartscreener
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python manage.py migrate
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Access the application at `http://127.0.0.1:8000/smartscreener/`

## Configuration

### API Configuration

For real-time data access, you need to configure your API credentials in the application:

1. Create a `.env` file in the project root with the following variables:
   ```
   PSX_API_USERNAME=your_username
   PSX_API_PASSWORD=your_password
   ```

2. Alternatively, you can set these as environment variables on your system.

## Project Structure

- `apps/SmartScreener/` - Main application code
  - `views.py` - API endpoints and view functions
  - `models.py` - Database models
  - `urls.py` - URL routing
- `static/SmartScreener/` - Static assets (CSS, JavaScript)
  - `js/screener.js` - Front-end JavaScript code
  - `css/styles.css` - Custom styling

## API Endpoints

The application provides the following API endpoints:

- `/smartscreener/api/get_stock_prices/` - Get current stock prices
- `/smartscreener/api/get_indices_live/` - Get live market indices
- `/smartscreener/api/get_psx_announcements/` - Get PSX announcements
- `/smartscreener/api/get_news/` - Get market news
- `/smartscreener/api/get_commodities/` - Get commodity prices
- `/smartscreener/api/get_currencies_live/` - Get live currency exchange rates
- `/smartscreener/api/get_economic_data/` - Get economic indicators
- `/smartscreener/api/get_technical_indicators/` - Get stock technical indicators
- `/smartscreener/api/get_stock_daily_history/` - Get stock price history
- `/smartscreener/api/screener/` - Advanced stock screening API

## Development

### Adding New Filters

To add a new filter to the screener:

1. Update the HTML form in the template to include the new filter
2. Add the filter logic to the `filter_stocks` function in `views.py`
3. Update the JavaScript code to include the new filter in requests

### Mock Data

The application includes mock data generators for development and testing purposes. These are used automatically when the API is unavailable.

To modify mock data:

1. Update the relevant mock data generation functions in `views.py`
2. Or modify the `loadMockData` function in `screener.js` for front-end testing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/) - The web framework used
- [jQuery](https://jquery.com/) - JavaScript library
- [Pakistan Stock Exchange](https://www.psx.com.pk/) - Data source
