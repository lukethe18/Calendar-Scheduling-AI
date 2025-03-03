import os
import openai
import datetime
import json 
import google.oauth2.credentials
import pytz
import sys

from flask import Flask, request, jsonify, redirect, render_template, url_for, g, flash
from flask_scss import Scss
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DateTimeLocalField, SubmitField, TextAreaField, HiddenField
from functools import wraps

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['DEBUG'] = True


SECRET_KEY = os.environ.get("SECRET_KEY")
openai.api_key = os.getenv("OPEN_API_KEY")
app.config['SECRET_KEY'] = SECRET_KEY or "Supercalifragilisticexpialidocious"
csrf = CSRFProtect(app)
Scss(app)

class EventForm(FlaskForm):  #pulling relevent information from the html
    timezone = HiddenField()
    description = TextAreaField("Description", render_kw=dict(rows=4, cols=50))
    submit = SubmitField("Create Event")

openai.api_key = os.getenv("OPEN_API_KEY")

# Google Calendar API Scopes
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/calendar.events"]


def require_valid_credentials(func):
    """
    A decorator that checks if token.json exists and contains valid credentials
    with a refresh token. If not, redirects the user to the /authorize route.
    Otherwise, attaches the credentials to flask.g and calls the route.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token_file = "token.json"
        if not os.path.exists(token_file):
            return redirect(url_for("authorize"))
        
        # Load credentials from token.json
        with open(token_file, "r") as token:
            creds_info = json.load(token)
        
        try:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_info(
                creds_info, scopes=SCOPES
            )
        except Exception as e:
            print("Error loading credentials:", e)
            return redirect(url_for("authorize"))
        
        # Check if credentials are valid and include a refresh token
        if not creds.valid or not creds.refresh_token:
            return redirect(url_for("authorize"))
        
        # Optionally, attach the credentials to flask.g for easy access in the route
        g.creds = creds
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def start():
    return render_template("index.html")

@app.route("/authorize")
def authorize():
    form = EventForm()
    token_file = "token.json"
    # Force re-consent if credentials are missing or invalid
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
    
    # Save the new credentials to token.json
    with open(token_file, "w") as token:
        token.write(creds.to_json())
    
    return redirect(url_for('create_event'))


@app.route("/events", methods=["GET"]) #Returns a JSON file of upcoming events, still in development
@require_valid_credentials
def get_events():
    """ Fetch upcoming events for the next 7 days and updates events.json."""

    creds = g.creds
    service = build("calendar", "v3", credentials = creds)

    # Define range for next 7 days
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0) 
    seven_days_later = now + datetime.timedelta(days=7)

    #format datetimes for API
    now_str = now.isoformat().replace("+00:00", "Z") 
    seven_days_later_str = seven_days_later.isoformat().replace("+00:00", "Z")

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now_str, 
        timeMax=seven_days_later_str, 
        singleEvents=True, 
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])

    # Save or update the events.json file
    with open("events.json", "w") as f:
        json.dump(events, f, indent = 4)

    
    return jsonify(events)

@app.route("/create_event", methods=["POST", "GET"])
@require_valid_credentials
def create_event():
    form = EventForm()

    if request.method == "GET":
        return render_template("form_chat.html", form=form)
    
    if request.method == "POST":
        if form.validate_on_submit():

            form_text = form.description.data
            user_timezone = form.timezone.data   

            try:
                # Loading current date information
                now = datetime.datetime.now(pytz.timezone(user_timezone))
                current_date_str = now.strftime("%Y-%m-%d")
                current_day_of_week = now.strftime("%A")

                prompt = f"""Today is {current_day_of_week}, {current_date_str}. Schedule an event using the following information '{form_text}'. 
                The user's timezone is {user_timezone}.
                
                Instructions:
                1. Provide a short clear summary title. 
                2. Provide a brief discriptoin. 
                3. Always suggest a start date and time *and* an end date and time.
                5. Return the start and end date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) 
                6. Be specific with times. For example, 'noon' means 12:00 p.m., 'midnight' means 12:00 a.m., and '6' would mean 6:00.
                7. End time *must* always be scheduled after start time. For example if the event information says 'from 8 to 6', assume 8 a.m. and 6 p.m. The start time must always come chronologically before the end time.
                8. If the description implies a duration, use it. If not, default to 1 hour. 
                9. If no time is given then scedule it for the entire day of the event. If it is an all day event then return 'true' for All Day Event:, if it is not an all day event, then return 'false'.
                10. Extract any location information from the description and include it in the response. If there is no explicit location information then provide 'unspecified for the 'Discription:' in the response.


                *   "Next Tuesday" means the *first* Tuesday that occurs *after* today.  Do not include the current day if it is already Tuesday.
                *   Other relative day names (e.g., "next Wednesday," "last Friday") should be interpreted similarly.
                """ 



                response = openai.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                     {"role": "system", "content": "You are a helpful calendar assistant. Return the following information: Summary: [summary] Location:[location] Description: [description] Start: [ISO 8601 start time] End: [ISO 8601 end time] All Day Event: [true or false]"},
                     {"role": "user", "content": prompt},
                 ],
                    max_tokens=100,
                )
                ai_suggestion = response.choices[0].message.content.strip()

                print(ai_suggestion, file=sys.stderr)


                try:
                    #Parses out relevent information from LLM response to create the calendar event
                    summary,location, description, start_time_str, end_time_str, all_day_event_str = parse_ai_suggestion(ai_suggestion)

                    print( f"The first try: {start_time_str}, {end_time_str}", file=sys.stderr)

                    if start_time_str and end_time_str: #Checks to ensure start_time_str and end_time_str are populated
                        start_time = datetime.datetime.fromisoformat(start_time_str) 
                        end_time = datetime.datetime.fromisoformat(end_time_str)

                        print( f"The first if statement: {start_time}, {end_time}", file=sys.stderr)

                        if end_time <= start_time: #Ensures start time is before end time
                            raise ValueError("Invalid time range: End time must be after start time.")

                        if all_day_event_str:
                            all_day_event = is_all_day_event(all_day_event_str)
                        else:
                            all_day_event = False 

                    else:
                        raise ValueError("Start time and end time not found")

                except ValueError as e:
                    return jsonify({"error": f"Could not parse AI suggestion: {e}. AI response: {ai_suggestion}"}), 400

                #creates calendar event based on if it is all day or not
                if all_day_event is True:
                    event = {
                        "summary": summary,
                        "description": description,
                        "location": location,
                        "start": {"date": start_time.strftime("%Y-%m-%d")},  
                        "end": {"date": end_time.strftime("%Y-%m-%d")},      
                     }   
                else:
                    event = {
                        "summary": summary,
                        "description": description,
                        "location": location,
                        "start": {"dateTime": start_time.isoformat()}, 
                        "end": {"dateTime": end_time.isoformat()},     
                        }

                #loads google credentials and submits the information to google calendar    
                creds = g.creds
                service = build("calendar", "v3", credentials=creds)
                created_event = service.events().insert(calendarId= "primary", body=event).execute()

                user_tz = pytz.timezone(user_timezone)
                local_start_time = start_time.astimezone(user_tz)
                local_end_time = end_time.astimezone(user_tz)

                print( f"Converting to local time: {local_start_time}, {local_end_time}", file=sys.stderr)

                local_start_str = local_start_time.strftime("%Y-%m-%d %I:%M %p %Z")
                local_end_str = local_end_time.strftime("%Y-%m-%d %I:%M %p %Z")

                return jsonify({
                            "message": (
                                f"Event created successfully!<br>"
                                f"Summary: {summary}<br>"
                                f"Description: {description}<br>"
                                f"Start Time: {local_start_str}<br>"
                                f"End Time: {local_end_str}"
                                      ),
                                "event_id": created_event["id"],
                                "Timezone": f"Collected user timezone is {user_timezone}"
                                }), 201
    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}")
            return redirect(url_for('create_event'), form=form)


def parse_ai_suggestion(ai_suggestion): # Helper function for parsing AI suggestions
    lines = ai_suggestion.splitlines()
    summary = None
    location_str = None
    description = None
    start_time = None
    end_time = None
    all_day_event_str = None

    for line in lines:
        if "Summary:" in line:
            summary = line.split("Summary:")[1].strip()
        elif "Location:" in line:
            location_str = line.split("Location:")[1].strip()
        elif "Description:" in line:
            description = line.split("Description:")[1].strip()
        elif "Start:" in line:
            start_time = line.split("Start:")[1].strip()
        elif "End:" in line:
            end_time = line.split("End:")[1].strip()
        elif "All Day Event:" in line:
            all_day_event_str = line.split("All Day Event:")[1].strip()    

    if not start_time or not end_time:
        raise ValueError("Could not find start or end time in AI suggestion.")

    return summary, location_str, description, start_time, end_time, all_day_event_str

def is_all_day_event(all_day_event_str): #checks if event is all day
    if all_day_event_str and all_day_event_str.lower() == "true":
        return True
    else:    
        return False

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5002)