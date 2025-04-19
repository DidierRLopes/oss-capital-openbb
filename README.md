# oss-capital-openbb

![CleanShot 2025-04-19 at 18 26 32](https://github.com/user-attachments/assets/24829b70-ff8e-4710-b7f8-ad4ad6b9717f)

![CleanShot 2025-04-19 at 18 30 58](https://github.com/user-attachments/assets/70b03e7d-5839-4f73-bb00-bf8b9264fca8)

Video: https://x.com/didier_lopes/status/1913710110838542515

## Setup and Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

### Environment Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On macOS/Linux:
```bash
source venv/bin/activate
```
- On Windows:
```bash
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following required environment variables:
```env
GITHUB_TOKEN=your_github_token_here
FMP_API_KEY=your_fmp_api_key_here
```

### Running the Application

1. Make sure your virtual environment is activated
2. Run the application using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

### Docker Alternative

If you prefer using Docker, you can build and run the application using:
```bash
docker build -t oss-capital-openbb .
docker run --env-file .env -p 8000:8000 oss-capital-openbb
```

## Environment Variables

- `GITHUB_TOKEN`: Your GitHub API token for authentication
- `FMP_API_KEY`: Your Financial Modeling Prep API key

Make sure to keep your `.env` file secure and never commit it to version control.
