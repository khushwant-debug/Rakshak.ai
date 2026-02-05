Rakshak.ai

Smart road accident detection demo (Flask + YOLOv8).

Quick start

1. Create a virtual environment and install requirements:

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r rakshak-ai/requirements.txt
```

2. Run the app:

```bash
python rakshak-ai/app.py
```

3. Open the dashboard at http://127.0.0.1:5000/

Notes
- Do NOT commit model weights (`models/*.pt`) to the repo; use Git LFS or download separately.
- To push to your GitHub repo, add the remote and push (example):

```bash
git init
git add .
git commit -m "Initial commit: rakshak-ai"
git remote add origin https://github.com/khushwant-debug/Rakshak.ai.git
git branch -M main
git push -u origin main
```

If you want, provide a GitHub Personal Access Token (PAT) and I can push this repo for you automatically, or run the commands above in your terminal to push locally.
