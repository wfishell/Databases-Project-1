from Packages import *

UserProfile = Blueprint('UserProfile', __name__, template_folder='templates')

@UserProfile.route('/userprofile/<username>', methods=['GET','POST'])
def UserPage(username):
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=f"""select cP.ProjectDescription, cp.ProjectID 
                                   from createproject cp inner join Users u on u.userid=cp.userid
                                    where u.username='{username}' order by cp.ParticipantsSoFar desc"""
        managed_projects = conn.execute(text(query)).fetchall()
        if not managed_projects:
              managed_projects=[('Currently Managing No Projects',)]
        query2=f"""    with UserJoinedProjects as(
                    select jp.projectid
                    from JoinProject jp
                    inner join Users u on u.userid=jp.userid
                    where u.username='{username}'
                    ),
                    ProjectNames as (
                    select cp.ProjectDescription, cp.projectid
                    from CreateProject cp
                    inner join UserJoinedProjects ujp on ujp.projectid=cp.projectid
                    )
                    Select *
                    From projectnames
                    Where ProjectDescription not in (
                    select cp.ProjectDescription
                    from CreateProject cp
                    inner join users u on u.userid=cp.userid
                    where u.username='{username}'
                    )"""
        joined_projects = conn.execute(text(query2)).fetchall()
        if not joined_projects:
              joined_projects=[('Currently on No Projects',)]
        conn.close()
        managed_project_description_list=[] 
        for project in managed_projects:
              managed_project_description_list.append(project)
        
        joined_project_description_list=[]
        for project in joined_projects:
              joined_project_description_list.append(project)
        
        return render_template('UserHomepage.html', username=username,managed_projects=managed_project_description_list,joined_projects=joined_project_description_list)

@UserProfile.route('/createproject/<username>', methods=['GET','POST'])
def createproject(username):
    if request.method == 'POST':
        Post_Username = username
        Post_Cat = str(request.form['Project_Category'])
        Post_Max_Part = str(request.form['Max_Part'])
        Post_Description = str(request.form['Project_Description'])
        Post_External_Project_Website=str(request.form['URL'])
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=f"SELECT userid FROM users WHERE username = '{Post_Username}'"
        userid = conn.execute(text(query)).fetchone()
        conn.close()
        if userid==None:
              flash('Please use a valid username.', 'error')
        else:
            userid=userid[0]
            conn = engine.connect()
            query2=f"SELECT max(projectid) FROM createproject"
            result2 = conn.execute(text(query2)).fetchone()
            conn.close()
            New_ProjectID=result2[0]+1
            try:
                query = f"""INSERT INTO CreateProject (
                    projectid, 
                    userid, 
                    projectorganizerid, 
                    projectcategory, 
                    MaxParticipantsNeeded, 
                    ParticipantsSoFar, 
                    ProjectDescription, 
                    URL
                    ) VALUES (
                    {New_ProjectID}, 
                    {userid}, 
                    {userid}, 
                    '{Post_Cat}', 
                    {int(Post_Max_Part)}, 
                    0, 
                    '{Post_Description}', 
                    '{Post_External_Project_Website}'
                    )"""
                conn = engine.connect()
                conn.execute(text(query))
                conn.commit()
                conn.close()
                return redirect(url_for('UserProfile.UserPage', username=username))
            except (IntegrityError, DataError, ValueError) as e:
                flash('Error signing up. Please try again.', 'error')
        conn.close()
    return render_template('createproject.html',username=username)