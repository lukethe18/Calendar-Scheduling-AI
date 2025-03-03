# AI Calendar Scheduler (Phase 1)

This is the first phase of a project aimed at developing an intelligent, agentic AI calendar scheduler. This initial stage focuses on creating a Flask-based application that leverages OpenAI's GPT models to interpret natural language input and schedule events in a user's Google Calendar.

## Project Description

This application allows users to describe their events in natural language (e.g., "Meeting next Tuesday from 10 to noon," "Doctor's appointment tomorrow at 2 pm") and have them automatically scheduled in their Google Calendar. The app uses OpenAI's GPT models to parse the input, extract relevant details (date, time, description, location), and convert them into the required format for the Google Calendar API.

**Technologies Used:**

* **Flask:** A Python web framework for building the application.
* **OpenAI GPT Models:** For natural language processing and event detail extraction.
* **Google Calendar API:** For creating and managing calendar events.
* **Python:** The primary programming language.
* **HTML, CSS, JavaScript:** For the user interface.
* **python-dotenv:** For managing environment variables in development.
* **pytz:** For timezone handling.
* **google-auth-oauthlib:** For google authentication.

**Challenges Faced:**

* **LLM Date and Time Interpretation:**
    * **Challenge:** Ensuring the LLM accurately interpreted and formatted dates and times, especially when dealing with relative dates ("tomorrow," "next week") and time ranges spanning midnight.
    * **Solution:** Refined the prompt with explicit instructions, clear examples, specific rules for handling relative dates, and time ranges across midnight. Added robust parsing to validate and sanitize LLM output.

* **Time Zone Conversions:**
    * **Challenge:** Consistently handling time zone independent of users location.
    * **Solution:** Implemented `pytz` for accurate time zone handling. Pulled the time zone from the web page and implemented it into the LLM's prompt. 

* **LLM Output Parsing:**
    * **Challenge:** Robustly parsing the LLM's output to handle variations in its responses and ensure correct data extraction.
    * **Solution:** Created a dedicated `parse_ai_suggestion` function to extract relevant information from the LLM's response. Added error handling and validation to gracefully handle unexpected output formats.

* **All-Day Events vs. Timed Events:**
    * **Challenge:** Properly differentiating and handling all-day events versus timed events.
    * **Solution:** Modified the prompt to explicitly request an "All Day Event" flag (true/false) in the LLM's response. Implemented conditional logic to create Google Calendar events using `date` fields for all-day events and `dateTime` fields for timed events.

* **Google API Authorization and Token Management:**
    * **Challenge:** Initially, the application successfully accessed the Google Calendar API after the first login and consent. However, subsequent API calls resulted in errors due to incomplete `token.json` credentials.
    * **Solution:** Modified the authorization flow to *always* require Google consent, ensuring that the `token.json` file contains all necessary fields. Implemented a Flask wrapper (`require_valid_credentials`) to check the `token.json` file for required fields on each page load, redirecting users to the authorization page if needed.


## Installation and Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/lukethe18/ai_calendar_scheduler.git](https://github.com/your_username/ai_calendar_scheduler.git)
    cd ai_calendar_scheduler
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv  # or python -m venv venv on Windows
    ```

3.  **Activate the Virtual Environment:**
    * Linux/macOS: `source venv/bin/activate`
    * Windows: `venv\Scripts\activate`

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up API Keys and Credentials:**
    * **OpenAI API Key:** Set the `OPEN_API_KEY` environment variable. For example:
        * Linux/macOS: `export OPEN_API_KEY="your_actual_api_key"`
        * Windows: `set OPEN_API_KEY="your_actual_api_key"`
    * **Google Calendar API Credentials:**
        * Create a Google Cloud project and enable the Google Calendar API.
        * Download your `credentials.json` file and place it in the project's root directory. **Do not commit this file to your repository.**
        * The application will prompt you to authorize access to your Google Calendar the first time you run it. This will generate a `token.json` file. **Do not commit this file to your repository.**

6. **Run the Application:**
    ```bash
    flask run -p 5002 # or whatever port you want to use.
    ```

7.  Open your web browser and navigate to `http://127.0.0.1:5002/`.

## Usage

1.  **Describe Your Event:** Enter a natural language description of your event in the provided text area.
2.  **Submit:** Click the "Create Event" button.
3.  **View Your Schedule:** Click the "View Schedule" button to see your upcoming events.

## Future Development

This is the first phase of a larger project. Future iterations will focus on:

* Developing an agentic AI program capable of managing various tasks and projects.
* Implementing intelligent scheduling based on task importance and user preferences.
* Enabling the system to learn and adapt over time, optimizing scheduling for individual users.
* Expanding scheduling functions to include project management, task prioritization, and time tracking.

## License

[Apache 2.0)]
