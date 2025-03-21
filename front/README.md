# moonvpn Bot Frontend

A modern React-based dashboard for managing the moonvpn Bot Telegram bot.

## Features

- 🌐 Multi-language support (English and Persian)
- 📱 Responsive design for all devices
- 🎨 Modern and clean UI
- 🔄 Real-time updates
- 🔒 Secure authentication
- 📊 Dashboard with key metrics
- 💰 Points management system
- ⚙️ User settings

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory and add the following variables:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_TELEGRAM_BOT_USERNAME=your_bot_username
```

## Development

Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Building for Production

Build the application:
```bash
npm run build
```

The production build will be created in the `build` directory.

## Project Structure

```
src/
├── components/         # React components
│   ├── dashboard/     # Dashboard components
│   ├── layout/        # Layout components
│   └── points/        # Points system components
├── locales/           # Translation files
│   ├── en/           # English translations
│   └── fa/           # Persian translations
├── styles/           # Global styles
├── App.js            # Main application component
└── index.js          # Application entry point
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 