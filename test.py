import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_text(prompt):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

prompt = "Once upon a time,"
generated_text = generate_text(prompt)
print(generated_text)

"""def create_events():
    creds = g.creds
    service = build("calendar", "v3", credentials = creds)
    form = CreateEventForm()
    if form.validate_on_submit():

        try:
            event_data = {
             'summary': form.summary.data,
             'start': {'dateTime': form.start_time.data.isoformat(), 'timeZone':'UTC'},
             'end': {'dateTime': form.end_time.data.isoformat(), 'timeZone': 'UTC'},
             'attendees': [{'email': email.strip()} for email in form.attendees.data.split(',')] if form.attendees.data else[]  # Optional attendees
                }
            
            event = service.events().insert(calendarId='primary', body=event_data).execute()
            return jsonify({"message": "Event created", "event_id": event['id']}), 201
    
        except Exception as e:
            print("Error creating event:", e)
            return jsonify({"error": str(e)}), 500 
    
    return render_template("form_chat.html", form=form)"""