Deployment options for Food Recommender System

This repository contains a Streamlit app `a.py` and dataset `VYAKULA.csv`.

Options to deploy:

1) Local Docker (quick, portable)

- Build image:
```powershell
cd "c:\Users\hp\Desktop\LOVE\SOUL\PROFESSION\DATA SCIENCE\FIELD\PROJECTS\Food recommender system"
docker build -t food-recommender:latest .
```

- Run container (map port 8501):
```powershell
docker run -p 8501:8501 --env FR_ADMIN_EMAIL="hoseatumaini12@gmail.com" --env FR_ADMIN_PASSWORD="<your_password>" -v "%CD%/VYAKULA.csv:/app/VYAKULA.csv" food-recommender:latest
```

Then open http://localhost:8501

Notes:
- Mount your `VYAKULA.csv` into the container to preserve the dataset and avoid copying large files into images.
- Provide SMTP credentials via env vars `FR_ADMIN_EMAIL` and `FR_ADMIN_PASSWORD`.

2) Render.com (Docker or repo service)

- Create a new Web Service on Render and connect your GitHub repo.
- Use the Docker option and set the `PORT` to `8501` (Render sets PORT automatically).
- Add environment variables `FR_ADMIN_EMAIL` and `FR_ADMIN_PASSWORD` in the Render dashboard.

3) Streamlit Community Cloud (simplest for public apps)

- Push this repository to GitHub.
- On https://share.streamlit.io, deploy new app from your GitHub repo pointing to `a.py`.
- Add secrets for `FR_ADMIN_EMAIL` and `FR_ADMIN_PASSWORD` via Streamlit Secrets (recommended) or use GitHub Actions to set them.
- Note: Streamlit Cloud expects the repo to be public for free usage.

4) Heroku (legacy; works if you still have an account)

- Create a Heroku app, set buildpack to Python, add `Procfile` (included) and push your repo.
- Set config vars for `FR_ADMIN_EMAIL` and `FR_ADMIN_PASSWORD`.

Tips & security
- Do not commit real SMTP passwords to the repo. Use environment variables or a secrets manager.
- The `goal_history/` folder is ignored by `.dockerignore` to avoid shipping user history in the image.

If you want, I can:
- Create a GitHub Actions workflow to build and push a Docker image to a registry (needs your registry credentials as GitHub secrets).
- Prepare a Render/Heroku deploy config automatically.
- Help you push the repo to GitHub and set up Streamlit Community Cloud (you'll need to authorize and add secrets).
