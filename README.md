## TeleWebSaver – Minimal Telegram Web Saver Bot

TeleWebSaver is a minimal Telegram bot that:

- Searches the web via a self‑hosted SearxNG instance.
- Shows the top 5 results as inline buttons (titles + domains).
- Downloads the selected page, renders it via headless Chromium, and sends a **PDF snapshot**.

Built with **Python 3.10+**, **aiogram v3**, **requests**, and **Playwright**. No database or web framework required.

**Requirements**:

- Docker and Docker Compose (**recommended**), or
- Python 3.10+ and system dependencies for Chromium/Playwright (if running locally).

---

### 1. Installation (local, optional)

You can run everything via Docker (see section 4). This section is only if you want to run the bot directly on your machine.

#### 1.1. Create and activate a virtual environment

```bash
cd TeleWebSaver
python3 -m venv .venv
source .venv/bin/activate  # on macOS / Linux
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

#### 1.2. Install dependencies

```bash
pip install --upgrade pip
pip install aiogram requests python-decouple playwright
python -m playwright install chromium
```

---

### 2. Environment variables

TeleWebSaver reads configuration from environment variables:

- **TELEGRAM_BOT_TOKEN** (required): your Telegram bot token obtained from BotFather.
- **SEARXNG_URL** (optional): base URL of your SearxNG instance. Defaults to `http://localhost:8080` for local runs.  
  When using `docker-compose`, this is automatically set to `http://searxng:8080` for the bot container.

You can provide them either as real environment variables or via a `.env` file using **python-decouple**.

#### 3.1. Using a `.env` file (recommended for local dev)

Create a file named `.env` in the project root (`TeleWebSaver`):

```env
TELEGRAM_BOT_TOKEN=1234567890:YOUR_BOT_TOKEN_HERE
# Optional, only needed if not using docker-compose defaults
SEARXNG_URL=http://localhost:8080
```

The bot uses `python-decouple` (`config(...)`), so these values will be read automatically from `.env` or from the OS environment if set.

#### 2.2. Setting environment variables manually (macOS / Linux – bash / zsh)

```bash
export TELEGRAM_BOT_TOKEN="1234567890:YOUR_BOT_TOKEN_HERE"
export SEARXNG_URL="http://localhost:8080"  # optional
```

#### 2.3. Example (Windows – PowerShell)

```powershell
$env:TELEGRAM_BOT_TOKEN="1234567890:YOUR_BOT_TOKEN_HERE"
$env:SEARXNG_URL="http://localhost:8080"   # optional
```

---

### 3. Running the bot locally (without Docker)

From the project directory (with virtualenv activated and dependencies installed):

```bash
cd TeleWebSaver
export TELEGRAM_BOT_TOKEN="1234567890:YOUR_BOT_TOKEN_HERE"
export SEARXNG_URL="http://localhost:8080"  # or your SearxNG URL
python main.py
```

You must also have a running SearxNG instance reachable at `SEARXNG_URL` (see section 4 for a Docker-based SearxNG).

If everything is set up correctly, you should see log messages like:

```text
INFO telewebsaver.app: Starting TeleWebSaver bot...
```

Then open Telegram, find your bot, and start chatting.

---

### 4. Running everything with Docker & docker-compose (recommended)

The repository includes a `Dockerfile` and `docker-compose.yml` that start:

- A SearxNG service, configured via `settings.yml`.
- The TeleWebSaver bot service, built from this project, using Playwright’s Chromium inside the container.

#### 4.1. Prepare `.env`

In the project root:

```env
TELEGRAM_BOT_TOKEN=1234567890:YOUR_BOT_TOKEN_HERE
```

#### 4.2. Start both SearxNG and the bot

From the project directory:

```bash
docker-compose up --build
```

This will:

- Build the `telewebsaver-bot` image (installs Python deps + Playwright Chromium).
- Start the `searxng` container with `settings.yml`.
- Start the `bot` container with `SEARXNG_URL` pointing to `http://searxng:8080`.

Once containers are up, your bot is ready to use in Telegram. You don’t need to install Python, Playwright, or SearxNG on the host.

---

### 5. Usage examples

- **Start / help**

  Send:

  ```text
  /start
  ```

  The bot replies with a short help message explaining how to search.

- **Search**

  Send:

  ```text
  /search python telegram bot tutorial
  ```

  The bot will:

  1. Send a “در حال جستجو... ⏳” message.
  2. Query SearxNG via its JSON API.
  3. Show the top 5 results as buttons, each labeled with the page title and its domain.

  When you press a button:

  - The bot uses **Playwright (headless Chromium)** to render the page and export it as a **PDF**.
  - The PDF file name is based on the page’s title (sanitized), e.g. `Uniform_Cost_Search_in_AI.pdf`.
  - Sends the PDF as a Telegram document.
  - Deletes the temporary PDF file afterwards.

  To view the page, simply download the PDF from Telegram and open it in any PDF viewer.

---

### 6. Contributing & issues

Contributions are welcome:

- **Issues**: If you find a bug or have a feature request (for example better cookie handling, new output formats, or configuration options), please open a GitHub issue with details and steps to reproduce if applicable.
- **Pull requests**: Fork the repository, create a feature or fix branch, and open a pull request describing:
  - What you changed
  - Why you changed it
  - How to test it (commands, sample `/search` queries, etc.)

For larger changes, it’s helpful to start with an issue or discussion first so we can agree on the approach.