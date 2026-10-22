# Recipe Hugging Face uses to build and start the app on its server.

FROM python:3.13-slim

# Hugging Face runs the app as a normal user with id 1000 (not as admin).
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

# Install the Python packages first, so Hugging Face can reuse this step
# when only the app code changes.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the app code. The app writes tribology.db, raw_data_settings.json
# and ai_model.json into backend/, so the folder must belong to "user".
COPY --chown=user . .

# Hugging Face sends visitors to port 7860.
EXPOSE 7860

# --no-token: no extra marimo password, because the Space itself is private
# (only people you give access to on Hugging Face can open it).
CMD ["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "7860", "--headless", "--no-token"]
