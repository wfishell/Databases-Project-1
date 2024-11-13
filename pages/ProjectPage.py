from Packages import *

project = Blueprint('project', __name__, template_folder='templates')

@project.route('/project/<int:project_id>/add_post', methods=['GET', 'POST'])
def project_page(project_id):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    user_id = session.get('user_id')
    project_query = text("""
        SELECT
            CP.ProjectID,
            CP.ProjectOrganizerID,
            U.UserName AS OrganizerUserName,
            CP.ProjectCategory,
            CP.MaxParticipantsNeeded,
            CP.ParticipantsSoFar,
            CP.ProjectDescription,
            CP.URL
        FROM CreateProject CP
        LEFT JOIN Users U ON U.UserID = CP.ProjectOrganizerID
        WHERE CP.ProjectID = :project_id
    """)
    project = conn.execute(project_query, {'project_id': project_id}).fetchone()
    if not project:
        conn.close()
        return "Project not found", 404

    user_id = session.get('user_id')

    is_member = False
    if user_id:
        member_query = text("""
            SELECT 1 FROM JoinProject
            WHERE UserID = :user_id AND ProjectID = :project_id
        """)
        result = conn.execute(member_query, {'user_id': user_id, 'project_id': project_id}).fetchone()
        if result or user_id == project[1]:
            is_member = True

    if request.method == 'POST' and not is_member:
        if not user_id:
            try:
                join_query = text("""
                    INSERT INTO JoinProject (ProjectID, UserID)
                    VALUES (:project_id, :user_id)
                """)
                conn.execute(join_query, {'project_id': project_id, 'user_id': user_id})
                update_participants_query = text("""
                    UPDATE CreateProject
                    SET ParticipantsSoFar = ParticipantsSoFar + 1
                    WHERE ProjectID = :project_id
                """)
                conn.execute(update_participants_query, {'project_id': project_id})
                conn.commit()
                flash('Successfully joined the project!', 'success')
                is_member = True
            except IntegrityError:
                flash('You have already joined this project.', 'error')

    posts_query = text("""
        SELECT P.PostID, P.PostTitle, P.PostContents, P.PostDate, P.IsQuestion, 
               COUNT(DISTINCT H.UserID) AS HeartCount
        FROM Post P
        LEFT JOIN HeartReact H ON P.ProjectID = H.ProjectID AND P.PostID = H.PostID
        WHERE P.ProjectID = :project_id
        GROUP BY P.PostID, P.PostTitle, P.PostContents, P.PostDate, P.IsQuestion
        ORDER BY P.PostDate DESC
    """)
    
    posts = conn.execute(posts_query, {'project_id': project_id}).fetchall()
    hearts_query = text("""
        SELECT P.PostID, H.UserID
        FROM Post P
        INNER JOIN HeartReact H ON P.ProjectID = H.ProjectID AND P.PostID = H.PostID
        WHERE P.ProjectID = :project_id
        ORDER BY P.PostDate DESC
    """)
    hearts = conn.execute(hearts_query, {'project_id': project_id}).fetchall()

    comments_query = text("""
        SELECT C.CommentID, C.PostID, C.CommentContents, C.Date
        FROM Comment C
        WHERE C.ProjectID = :project_id
        ORDER BY C.Date ASC
    """)
    comments = conn.execute(comments_query, {'project_id': project_id}).fetchall()
   
    comments_by_post = {}
    for comment in comments:
        comments_by_post.setdefault(comment[1], []).append(comment)

    participants_query = text("""
        SELECT U.UserID, U.UserName
        FROM Users U
        INNER JOIN JoinProject JP ON U.UserID = JP.UserID
        WHERE JP.ProjectID = :project_id
        UNION
        SELECT U.UserID, U.UserName
        FROM Users U
        INNER JOIN CreateProject CP ON U.UserID = CP.ProjectOrganizerID
        WHERE CP.ProjectID = :project_id
    """)
    participants = conn.execute(participants_query, {'project_id': project_id}).fetchall()
    conn.close()
    return render_template('Projects.html', project=project, is_member=is_member, posts=posts, hearts=hearts,comments_by_post=comments_by_post, participants=participants,user_id=user_id)

@project.route('/project/<int:project_id>/post/<int:post_id>/comment', methods=['POST'])
def add_comment(project_id, post_id):
    user_id = session.get('user_id')
    Check=CheckIfUserOnProject(user_id, project_id)
    if Check==0:
        flash('You need to join the project first', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    comment_contents = str(request.form['comment_contents'])
    if not comment_contents.strip():
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))

    comment_id_query = text("""
        SELECT COALESCE(MAX(CommentID), 0) + 1 FROM Comment
        WHERE ProjectID = :project_id AND PostID = :post_id
    """)
    new_comment_id = conn.execute(comment_id_query, {'project_id': project_id, 'post_id': post_id}).scalar()

    insert_comment_query = text("""
        INSERT INTO Comment (CommentID, PostID, ProjectID, CommentContents, Date, DirectCommentID, ReplyID)
        VALUES (:comment_id, :post_id, :project_id, :content, Current_Date, 1, NULL)
    """)
    try:
        conn.execute(insert_comment_query, {
            'comment_id': new_comment_id,
            'post_id': post_id,
            'project_id': project_id,
            'content': comment_contents
        })
        conn.commit()
        flash('Comment added successfully.', 'success')
    except Exception as e:
        flash('Failed to add comment.', 'error')
    conn.close()
    return redirect(url_for('project.project_page', project_id=project_id))

@project.route('/project/<int:project_id>/join', methods=['GET','POST'])
def join_project(project_id):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    user_id = session.get('user_id')
    Check=CheckIfUserOnProject(user_id, project_id)
    if Check!=0:
        flash('You have already joined this project', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    CurrentParticipants = text("""
            Select MaxParticipantsNeeded-ParticipantsSoFar
            From CreateProject
            where projectid= :project_id
        """)
    NumSpots=conn.execute(CurrentParticipants,{'project_id':project_id}).scalar()
    if NumSpots==0:
        flash('There are no spots left for this project','error')
        return redirect(url_for('project.project_page', project_id=project_id))
    
    insert_query = text("""
            INSERT INTO JoinProject (UserID, ProjectID)
            VALUES (:user_id, :project_id)
        """)
    update_project_members=text("""
            UPDATE CreateProject
            SET ParticipantsSoFar=ParticipantsSoFar+1
            Where ProjectID=:project_id""")
    try:
        conn.execute(insert_query, {'user_id': user_id, 'project_id': project_id})
        conn.commit()
        conn.execute(update_project_members,{'project_id':project_id})
        conn.commit()
        flash('Joined Project!', 'success')
    except Exception as e:
        flash('Failed to Join Project', 'error')
    conn.close()
    return redirect(url_for('project.project_page', project_id=project_id))
    
@project.route('/project/<int:project_id>/post/<int:post_id>/heart', methods=['GET','POST'])
def add_remove_heart(project_id, post_id):
    user_id = session.get('user_id')
    Check=CheckIfUserOnProject(user_id, project_id)
    if Check==0:
        flash('You need to join the project first', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))

    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))

    check_query = text("""
        SELECT 1 FROM HeartReact
        WHERE UserID = :user_id AND ProjectID = :project_id AND PostID = :post_id
    """)
    result = conn.execute(check_query, {'user_id': user_id, 'project_id': project_id, 'post_id': post_id}).fetchone()
    if result:
        delete_query = text("""
            DELETE From HeartReact
            Where (UserId=:user_id and PostId=:post_id and ProjectID=:project_id)
        """)
        try:
            conn.execute(delete_query, {'user_id': user_id, 'post_id': post_id, 'project_id': project_id})
            conn.commit()
            flash('Heart react removed successfully.', 'success')
        except Exception as e:
            flash('Failed to remove heart react.', 'error')
    else:
        insert_query = text("""
            INSERT INTO HeartReact (UserID, PostID, ProjectID)
            VALUES (:user_id, :post_id, :project_id)
        """)
        try:
            conn.execute(insert_query, {'user_id': user_id, 'post_id': post_id, 'project_id': project_id})
            conn.commit()
            flash('Heart react added successfully.', 'success')
        except Exception as e:
            flash('Failed to add heart react.', 'error')
    conn.close()
    return redirect(url_for('project.project_page', project_id=project_id))

@project.route('/project/<int:project_id>', methods=['GET','POST'])
def add_post(project_id):
    user_id = session.get('user_id')
    Check=CheckIfUserOnProject(user_id, project_id)
    if Check==0:
        flash('You need to join the project first', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    
    post_title = str(request.form['post_title'])
    if not post_title.strip():
        flash('Post Title cannot be empty.', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    
    post_contents = str(request.form['post_contents'])
    if not post_contents.strip():
        flash('Post Contents cannot be empty.', 'error')
        return redirect(url_for('project.project_page', project_id=project_id))
    
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    is_question = request.form.get('is_question')
    if is_question:
        is_question=True
    else:
        is_question=False

    post_id_query= text("""
        SELECT (COALESCE(MAX(PostID), 0))+1
        FROM POST
        WHERE ProjectID=:project_id
    """)
    post_id = conn.execute(post_id_query, {'project_id': project_id}).scalar()
    print(project_id,'projectid')
    print(post_id,'postid')
    post_query = text("""
        INSERT INTO POST(ProjectID, PostID, PostTitle, PostContents, PostDate, IsQuestion)
        VALUES (:project_id, :post_id, :post_title, :post_contents, current_date, :is_question)
    """)
    try:
        conn.execute(post_query, {
            'project_id': project_id,
            'post_id': post_id,
            'post_title': post_title,
            'post_contents': post_contents,
            'is_question': is_question
        })
        conn.commit()
        flash('Post added successfully.', 'success')
    except  IntegrityError as e:
        flash('Failed to add post.', 'error')
    conn.close()
    return redirect(url_for('project.project_page', project_id=project_id))

def CheckIfUserOnProject(userid, projectid):
    conn = engine.connect()
    conn.execute(text("SET SCHEMA 'wf2322'"))
    ProjectCheck = text("""
                WITH Managed_Project AS (
                    SELECT cp.projectid
                    FROM users U 
                    INNER JOIN createproject cp ON cp.userid = u.userid
                    WHERE u.userid = :user_id AND cp.projectid = :project_id
                ),
                Joined_Project AS (
                    SELECT jp.projectid
                    FROM users U 
                    INNER JOIN joinproject jp ON jp.userid = u.userid
                    WHERE u.userid = :user_id AND jp.projectid = :project_id
                ),
                Total AS (
                    SELECT *
                    FROM Managed_Project
                    UNION
                    SELECT *
                    FROM Joined_Project
                )
                SELECT COUNT(*)
                FROM Total
                """)
    
    ProjectCheck = conn.execute(ProjectCheck, {
            'user_id': userid,
            'project_id': projectid
    }).scalar()
    
    conn.close()  
    return ProjectCheck