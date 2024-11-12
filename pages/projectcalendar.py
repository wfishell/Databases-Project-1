from Packages import *
from datetime import datetime, timedelta

projectcalendar = Blueprint('projectcalendar', __name__, template_folder='templates')

@projectcalendar.route('/projectcalendar/<int:project_id>', methods=['GET', 'POST'])
def calendar_page(project_id):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    user_id = session.get('user_id')

    calendar_query = text("""
        SELECT CalendarID FROM ProjectCalendar
        WHERE ProjectID = :project_id
    """)
    result = conn.execute(calendar_query, {'project_id': project_id}).scalar()

    if result:
        print(result, 'calendarid')
        calendar_id = result
    else:
        new_calendar_id=101
        insert_calendar_query = text("""
            INSERT INTO ProjectCalendar (ProjectID, CalendarID)
            VALUES (:project_id, :calendar_id)
        """)
        conn.execute(insert_calendar_query, {'project_id': project_id, 'calendar_id': new_calendar_id})
        conn.commit()
        return redirect(url_for('projectcalendar.calendar_page', project_id=project_id))

    events_query = text("""
        SELECT EventID, StartTime, EndTime, IsRecurring, EventTitle
        FROM Event
        WHERE ProjectID = :project_id AND CalendarID = :calendar_id
    """)
    events = conn.execute(events_query, {'project_id': project_id, 'calendar_id': calendar_id}).mappings().all()

    today = datetime.today()
    start_of_month = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)
    date_range = []
    current_date = start_of_month
    while current_date < next_month:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    conn.close()
    return render_template('calendar.html', project_id=project_id, events=events, date_range=date_range)

@projectcalendar.route('/projectcalendar/<int:project_id>/event', methods=['GET', 'POST'])
def add_event(project_id):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    user_id = session.get('user_id')
    calendar_id = text("""
        SELECT max(CalendarID)
        FROM ProjectCalendar
        WHERE ProjectID = :project_id 
    """)
    calendar_id = conn.execute(calendar_id, {'project_id': project_id}).scalar()

    if request.method == 'POST':
        event_title = request.form.get('event_title')
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        is_recurring = True if request.form.get('is_recurring') else False

        if not event_title or not start_date or not start_time or not end_date or not end_time:
            flash('Please fill in all the fields', 'error')
            return redirect(url_for('projectcalendar.calendar_page', project_id=project_id))
        start_datetime_str = f"{start_date} {start_time}"
        end_datetime_str = f"{end_date} {end_time}"
        try:
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
            if start_datetime>=end_datetime or start_datetime<datetime.now():
                flash('Please use a proper date range for the meeting', 'error')
                return redirect(url_for('projectcalendar.calendar_page', project_id=project_id))
        except ValueError:
            flash('Invalid date/time format', 'error')
            return redirect(url_for('projectcalendar.calendar_page', project_id=project_id))

        new_event_id_query = text("""
            SELECT COALESCE(MAX(EventID), 0) + 1 FROM Event
            WHERE ProjectID = :project_id AND CalendarID = :calendar_id
        """)
        event_id = conn.execute(new_event_id_query, {'project_id': project_id, 'calendar_id': calendar_id}).scalar()

        insert_event_query = text("""
            INSERT INTO Event (EventID, ProjectID, CalendarID, StartTime, EndTime, IsRecurring, EventTitle)
            VALUES (:event_id, :project_id, :calendar_id, :start_time, :end_time, :is_recurring, :event_title)
        """)
        try:
            conn.execute(insert_event_query, {
                'event_id': event_id,
                'project_id': project_id,
                'calendar_id': calendar_id,
                'start_time': start_datetime,
                'end_time': end_datetime,
                'is_recurring': is_recurring,
                'event_title': event_title
            })
            conn.commit()
            flash('Event added successfully', 'success')
        except Exception as e:
            flash('Failed to add event.', 'error')
            print(e)
        return redirect(url_for('projectcalendar.calendar_page', project_id=project_id))
