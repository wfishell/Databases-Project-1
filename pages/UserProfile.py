from Packages import *

UserProfile = Blueprint('UserProfile', __name__, template_folder='templates')

@UserProfile.route('/userprofile/<username>', methods=['GET','POST'])
def UserPage(username):
        session['username']=username
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=text(f"""select cP.ProjectDescription, cp.ProjectID 
                                   from createproject cp inner join Users u on u.userid=cp.userid
                                    where u.username='{username}' order by cp.ParticipantsSoFar desc""")
        managed_projects = conn.execute(query,{'username':username}).fetchall()
        if not managed_projects:
              managed_projects=[('Currently Managing No Projects',)]
        query2=text(f"""    with UserJoinedProjects as(
                    select jp.projectid
                    from JoinProject jp
                    inner join Users u on u.userid=jp.userid
                    where u.username=:username
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
                    where u.username=:username
                    )""")
        joined_projects = conn.execute(query2,{'username':username}).fetchall()
        potential_projects=[]
        if not joined_projects:
            joined_projects=[('Currently Joined No Projects',)]
            alternative_projects= text(f"""    
                with UserJoinedProjects as(
                select jp.projectid
                from JoinProject jp
                inner join Users u on u.userid=jp.userid
                where u.username= :username
                ),
                ProjectNames as (
                select cp.ProjectDescription, cp.projectid
                from CreateProject cp
                inner join UserJoinedProjects ujp on ujp.projectid=cp.projectid
                )
                Select cp.ProjectDescription, cp.ProjectID
                From createproject cp
                inner join Users U on cp.userid=u.userid
                where u.username!= :username
                limit 5
                """)
            potential_projects = conn.execute(alternative_projects,{'username':username}).fetchall()


        conn.close()
        managed_project_description_list=[] 
        for project in managed_projects:
              managed_project_description_list.append(project)
        
        joined_project_description_list=[]
        for project in joined_projects:
              joined_project_description_list.append(project)
            
        alternative_project_description_list=[]
        for project in potential_projects:
              alternative_project_description_list.append(project)

        
        return render_template('UserHomepage.html', username=username,managed_projects=managed_project_description_list,joined_projects=joined_project_description_list, alt_projects=alternative_project_description_list)

@UserProfile.route('/createproject/<username>', methods=['GET','POST'])
def createproject(username):
    if request.method == 'POST':
        Post_Username = username
        Post_Cat = str(request.form['Project_Category'])
        try:
            Post_Max_Part = int(request.form['Max_Part'])
        except:
             flash('You need to input a number, error')
             return redirect(url_for('UserProfile.createproject',username=username))
        Post_Description = str(request.form['Project_Description'])
        Post_External_Project_Website=str(request.form['URL'])
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=f"SELECT userid FROM users WHERE username = '{Post_Username}'"
        userid = conn.execute(text(query)).fetchone()
        if userid==None:
            flash('Please use a sign in', 'error')
            return redirect(url_for('UserProfile.createproject',username=username))
        else:
            userid=userid[0]
            conn = engine.connect()
            query2=f"SELECT max(projectid) FROM createproject"
            result2 = conn.execute(text(query2)).scalar()
            New_ProjectID=result2+1
            if not Post_Description or not Post_Cat:
                flash('Please describe the project, error')
                return redirect(url_for('UserProfile.createproject',username=username))

            if Post_Max_Part<=0:
                flash('You need to increase the number of participants!, error')
                return redirect(url_for('UserProfile.createproject',username=username))

            query = text(f"""
            INSERT INTO CreateProject (
                projectid, 
                userid, 
                projectorganizerid, 
                projectcategory, 
                MaxParticipantsNeeded, 
                ParticipantsSoFar, 
                ProjectDescription, 
                URL
            ) VALUES (
                :project_id, 
                :user_id, 
                :project_organizer_id, 
                :project_category, 
                :max_participants_needed, 
                :participants_so_far, 
                :project_description, 
                :url
                )""")
            try:
                conn.execute(query, {
                    'project_id': New_ProjectID,
                    'user_id': userid,
                    'project_organizer_id': userid,
                    'project_category': Post_Cat,
                    'max_participants_needed': Post_Max_Part,
                    'participants_so_far': 0,
                    'project_description': Post_Description,
                    'url': str(Post_External_Project_Website)
                })
                conn.commit()
                conn.close()
                return redirect(url_for('UserProfile.UserPage', username=username))
            except (IntegrityError, DataError, ValueError) as e:
                flash('Error signing up. Please try again.', 'error')
                return redirect(url_for('UserProfile.createproject',username=username))

        conn.close()
    return render_template('createproject.html',username=username)