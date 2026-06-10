# Deploying the Faculty Survey Portal to Streamlit Community Cloud

This guide walks you through publishing the app at a shareable URL
(e.g. `https://vumc-anesthesiology-survey.streamlit.app`). No prior Python
or Git experience required. Plan on ~25 minutes the first time.

> **What you will end up with.** A private password-protected web app hosted
> for free by Streamlit. You give the URL + password to authorized department
> personnel; they upload the REDCap CSV and download the report.

---

## Before you start

You will need:

1. The **`faculty_survey_app/`** folder (this folder) on your computer.
2. A web browser (Chrome, Safari, Edge, or Firefox).
3. ~25 minutes.
4. A password you want to use for the app (pick something memorable but
   non-obvious — e.g. a passphrase like `joyful-anesth-2026`).

---

## Step 1 — Create a free GitHub account (skip if you have one)

1. Go to **<https://github.com/signup>**.
2. Enter your work email, choose a username, choose a password, and click
   **Continue**.
3. Solve the puzzle/captcha, then click **Continue**.
4. Choose the **Free** plan. You don't need any of the paid features.
5. Open your email and click the verification link GitHub sent you.

You now have a GitHub account.

---

## Step 2 — Create a new GitHub repository

1. Sign in at **<https://github.com>**.
2. In the upper-right corner, click the **`+`** menu, then click **New
   repository**.
3. **Owner**: your username.
4. **Repository name**: type `vumc-anesthesiology-survey` (or any name you
   want — no spaces).
5. **Description** (optional): "VUMC Anesthesiology Faculty Survey portal".
6. **Visibility**: select **Public**. *(Streamlit Community Cloud requires
   public repos for the free tier. The data is never committed to the repo,
   and the app password is stored separately in Streamlit's encrypted secrets.)*
7. Check **Add a README file**.
8. Click the green **Create repository** button.

You now see an empty repository with one file (`README.md`).

---

## Step 3 — Upload the app files via the GitHub web UI

You do *not* need to install Git. You will drag and drop files into the
browser.

1. In your new repository, click the **Add file** button, then click
   **Upload files**.
2. In a separate window, open the **`faculty_survey_app/`** folder on your
   computer.
3. **Select these files and folders** and drag them into the GitHub upload
   area:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `DEPLOYMENT.md`
   - the `src/` folder (contains `analysis.py`, `chart_builder.py`,
     `division_report.py`, `longitudinal.py`, `report_builder.py`,
     `__init__.py`)
   - the `.streamlit/` folder (contains `config.toml`)

   > **Tip.** If `.streamlit/` is hidden in Finder, press
   > `Cmd + Shift + .` to show hidden folders. On Windows, in File Explorer
   > click **View → Show → Hidden items**.

   > **What NOT to upload.** Do not upload any REDCap CSV files. The data
   > stays on your computer (and on the Streamlit Cloud server only at
   > runtime when you upload it through the app).

4. Wait for the file list to appear. The status under each item should say
   "ready".
5. Scroll down. Under **Commit changes**, leave the default message
   (`Add files via upload`) and click the green **Commit changes** button.

You now see all the project files in your repository.

---

## Step 4 — Connect Streamlit Community Cloud

1. In a new browser tab, go to **<https://share.streamlit.io>**.
2. Click **Continue with GitHub** (or **Sign in**).
3. GitHub will ask you to authorize Streamlit to access your account.
   Click **Authorize streamlit**.
4. The first time you sign in, Streamlit may ask for your email and a few
   details. Fill them in and click **Continue**.

You now see the Streamlit Community Cloud dashboard.

---

## Step 5 — Deploy the app

1. Click the **Create app** button in the upper-right (it may also be
   called **New app**).
2. Choose **Deploy a public app from GitHub**.
3. Fill in:
   - **Repository**: pick `your-username/vumc-anesthesiology-survey`.
   - **Branch**: `main`.
   - **Main file path**: `app.py`.
   - **App URL**: pick something memorable, e.g.
     `vumc-anesthesiology-survey`. The full URL will be
     `https://vumc-anesthesiology-survey.streamlit.app`.
4. Click the **Advanced settings** link (below the form).
5. Set **Python version** to **3.11** if a dropdown is offered.
6. Under **Secrets**, paste exactly this (with your actual password):

   ```toml
   app_password = "your-password-here"
   ```

   Replace `your-password-here` with the password you chose at the start.
   Keep the quotation marks.
7. Click **Save** to close Advanced settings.
8. Click the **Deploy** button.

The app will now build (3–7 minutes the first time). You'll see a black
log window with installation messages — that's normal. When it finishes,
you'll see the password prompt.

---

## Step 6 — Verify the app works

1. After deployment finishes, the password screen appears.
2. Type the password you set in Step 5 → click **Sign in**.
3. In the left sidebar:
   - Drag a REDCap CSV onto the file uploader.
   - Type a year in the **Survey year** box (e.g. `2026`).
   - Click **Add year**.
4. The right side should show the snapshot tiles (n, MINI-Z, burnout, WBI,
   NPS).
5. Click **Generate 2026 Department Report**, wait for the spinner, then
   click **Download Word report (.docx)**.

If the Word file opens and looks right — you're done.

---

## Step 7 — Share the URL

Send these two items to authorized users:

- The URL: `https://your-app-name.streamlit.app`
- The password you set

---

## Updating the app later

If you change a Python file:

1. In the GitHub repository, click the file, then click the **pencil
   (Edit)** icon.
2. Paste the new contents, scroll down, and click **Commit changes**.
3. Streamlit Cloud will redeploy automatically within ~1 minute.

If you change the password:

1. In Streamlit Cloud, click your app's **⋯** menu → **Settings → Secrets**.
2. Edit the `app_password = "..."` line.
3. Click **Save**. The app restarts within seconds.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| App says "App password is not configured." | You skipped Step 5.6 — add `app_password = "..."` in Settings → Secrets. |
| "ModuleNotFoundError" in the build log | The repository may be missing a file from `src/`. Re-upload the `src/` folder via Step 3. |
| Long delay after clicking **Generate Report** | Normal for the first run on a fresh container (~30–60 s). Subsequent runs are faster. |
| Upload says "file too large" | Your REDCap CSV is over 50 MB (unlikely). Increase `maxUploadSize` in `.streamlit/config.toml` and redeploy. |
| Wrong year shows up after upload | The **Survey year** text box was empty when you clicked **Add year**. Remove the year via the sidebar and re-add it with the correct label. |

---

## Costs

Streamlit Community Cloud is free for public repositories. There is no
credit-card requirement. Apps sleep after ~7 days of inactivity but wake up
automatically when someone visits the URL (10–15 second delay on cold start).

---

## Privacy

- The REDCap CSV is uploaded from the user's browser into the running
  Streamlit container's RAM only. It is **never written to disk** by this app
  and is **never committed to GitHub**.
- The shared password is the only access control. Treat the URL + password
  combination as sensitive and rotate the password periodically.
- Streamlit Cloud terms: <https://streamlit.io/cloud-terms-of-service>.
