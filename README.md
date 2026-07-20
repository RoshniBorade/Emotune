# EMOTUNE 🎵

An emotion-driven music generation app that creates personalized songs based on your mood and preferences.

## Features

- 🎤 Generate Hindi lyrics based on emotions using Google Gemini AI
- 🎵 Create music with AI-generated audio matching your selected style
- 🎨 Beautiful dark-themed UI with animated waveform effects
- ⚡ Real-time task polling for music generation

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini API (Hindi lyrics generation)
- **Music Generation**: PiAPI (Qubico/ace-step model)
- **Backend**: Python

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/EMOTUNE.git
cd EMOTUNE
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   MUSIC_API_KEY=your_piapi_key_here
   MUSIC_API_URL=https://api.piapi.ai/api/v1/task
   ```

4. Run the application:
```bash
python -m streamlit run app.py
```

## Usage

1. Open `http://localhost:8501` in your browser
2. Enter an emotion or mood description
3. Select music styles/tags
4. Click "Generate" to create your personalized music
5. Wait for the AI to generate lyrics and compose the music

## API Keys Required

- **Google Gemini API**: https://aistudio.google.com/apikey
- **PiAPI Account**: https://piapi.ai (for music generation)

## Project Structure

```
EMOTUNE_2/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (not in repo)
├── utils/
│   ├── llm_api.py       # Google Gemini integration
│   └── music_api.py     # PiAPI music generation
└── README.md            # This file
```

## Contributing

Feel free to fork and submit pull requests!

## License

MIT License
