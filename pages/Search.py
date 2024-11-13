from Packages import *

Search = Blueprint('Search', __name__, template_folder='templates')

@Search.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form.get('Search')
        if search_term:
            conn = engine.connect()
            conn.execute(text("SET SCHEMA 'wf2322'"))
            query = text("""SELECT ProjectID, ProjectDescription
                            FROM CreateProject
                            WHERE ProjectDescription ILIKE :Search""")
            search_pattern = f'%{search_term}%'
            result = conn.execute(query, {'Search': search_pattern}).fetchall()
            conn.close()
            if not result:
                flash('No search results returned', 'error')
                result = []
        else:
            result = []
        return render_template('search.html', results=result)
    else:
        return render_template('search.html', results=[])

        