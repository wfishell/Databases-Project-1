from Packages import *
from datetime import datetime

projectcalendar = Blueprint('projectcalendar', __name__, template_folder='templates')

@projectcalendar.route('/projectcalendar/<int:project_id>', methods=['GET', 'POST'])
def calendar_page(project_id):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    user_id = session.get('user_id')
    date_range = text("""
        with nextmonth as(
            SELECT generate_series(1, 30) AS number),
            date as (select current_date as date)
            select date + (number - 1) as date
            from date
            cross join nextmonth
            order by date asc 
    """)
    project = conn.execute(date_range).fetchall()
    return render_template('calendar.html', project_id=project_id, date_range=date_range)