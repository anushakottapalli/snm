from flask import Flask,render_template,request,redirect,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
from cmail import send_mail
from stoken import endata,dedata
import mysql.connector
import flask_excel as excel 
from io import BytesIO #used to convert hexadecimal data into bytes
import re
from mimetypes import guess_type
mydb=mysql.connector.connect(user='root',password='anusha',host='localhost',db='snmdb')
app=Flask(__name__)
excel.init_excel(app) #initalization 
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='123456789'
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register',methods=['GET','POST'])  
def register():
    if request.method=="POST":
        username=request.form['username']  
        usermail=request.form['usermail']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where usermail=%s',[usermail])
        count_usermail=cursor.fetchone() #if account there (1,) and if no account (0,)
        if count_usermail[0]==0:
            gotp=genotp() #server generated otp
            userdata={'username':username,'usermail':usermail,'password':password,'otp':gotp}
            subject='OTP for simple notes management system'
            body=f"Hello {username},\n\nYour OTP code is: {gotp}\n\nThank you!"
            send_mail(to=usermail,subject=subject,body=body)
            flash(f'otp has been sent to given mail {usermail}')
            return redirect(url_for('otpverify',udata=endata(data=userdata))) # encrypting otp data
        elif count_usermail[0]==1:
            flash('usermail already exists')
            return redirect(url_for('register'))    
    return render_template('register.html')  
@app.route('/otpverify/<udata>',methods=['GET','POST'])   
def otpverify(udata):
    if request.method=='POST':
        user_otp=request.form['otp']
        de_userdata=dedata(data=udata) #decrytiping encrypted user data
        if de_userdata['otp']==user_otp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into user(username,usermail,password) values(%s,%s,%s)',[de_userdata['username'],de_userdata['usermail'],de_userdata['password']])
            mydb.commit()
            cursor.close()
            flash(f'Successfully registred pls login{de_userdata["username"]}')
            return  redirect(url_for('login.html'))
        else:
            flash('otp was wrong')
            return redirect(url_for('otpverify',udata=udata))
    return render_template('otp.html') 
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('user'):
        if request.method=="POST":
            login_usermail=request.form['usermail']
            login_password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where usermail=%s',[login_usermail])
            count_usermail=cursor.fetchone()
            print(count_usermail)
            if count_usermail[0]==1:
                cursor.execute('select password from user where usermail=%s',[login_usermail])
                stored_password=cursor.fetchone()
                if stored_password[0]==login_password:
                    session['user']=login_usermail
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('userlogin'))
            else:
                flash('email not found pls check')
                return redirect(url_for('userlogin'))
        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))      
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))   
@app.route('/userlogout')
def userlogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('userlogin'))
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))            
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=="POST":
            print(request.form)
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute('insert into notesdata(title,description,added_by)values(%s,%s,%s)',[title,description,user_id[0]])
            mydb.commit()
            flash('notes successfully added')
        return render_template('addnotes.html') 
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))   
@app.route('/view_allnotes')   
def view_allnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from user where usermail=%s',[session.get('user')])
        user_id=cursor.fetchone()
        cursor.execute('select notesid,title,created_at from notesdata where added_by=%s',[user_id[0]])
        stored_notesdata=cursor.fetchall()
        print(stored_notesdata)
        return render_template('view_allnotes.html',ndata=stored_notesdata)  
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))  
@app.route('/view_notes/<nid>')    
def view_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notesdata where notesid=%s',[nid])
        stored_notesdata=cursor.fetchone()
        print(stored_notesdata)
        return render_template('view_notes.html',
        stored_notesdata=stored_notesdata)
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))     
@app.route('/deletenotes/<nid>')    
def deletenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notesdata where notesid=%s',[nid])
        mydb.commit()
        cursor.close()
        flash('notes deleted successfully')
        return redirect(url_for('view_allnotes'))
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))  
@app.route('/update_notes/<nid>',methods=['GET','POST'])    
def update_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notesdata where notesid=%s',[nid])
        stored_notesdata=cursor.fetchone()
        print(stored_notesdata)
        if request.method=='POST':
            updated_title=request.form['title']
            updated_description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notesdata set title=%s,description=%s where notesid=%s',[updated_title,updated_description,nid])
            mydb.commit()
            cursor.close()
            flash('notes updated successfully')
            return redirect(url_for('view_notes',nid=nid))  
        return render_template('updatenotes.html',stored_notesdata=stored_notesdata)
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))    
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()  #we get the data in backend as byte format,and in database we get in hexadecimal format
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute('insert into file_data(filename,filedata,added_by)values(%s,%s,%s)',[fname,fdata,user_id[0]])
            mydb.commit()
            flash(f'{fname} file added successfully')
        return render_template('fileupload.html')
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))      
@app.route('/view_allfiles')   
def view_allfiles():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from user where usermail=%s',[session.get('user')])
        user_id=cursor.fetchone()
        cursor.execute('select fid,filename,created_at from file_data where added_by=%s',[user_id[0]])
        stored_filedata=cursor.fetchall()
        print(stored_filedata)
        return render_template('view_allfiles.html',fdata=stored_filedata)
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))     
@app.route('/view_file/<fid>')    
def view_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from file_data where fid=%s',[fid])
        fdata=cursor.fetchone()
        array_data=BytesIO(fdata[2])
        mime_type,_=guess_type(fdata[1])
        print(mime_type)
        return send_file(array_data,mimetype=mime_type or 'application/octat_stream',as_attachment=False,download_name=fdata[1])
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))    
@app.route('/download_file/<fid>')    
def download_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from file_data where fid=%s',[fid])
        fdata=cursor.fetchone()
        array_data=BytesIO(fdata[2])
        mime_type,_=guess_type(fdata[1])
        print(mime_type)
        return send_file(array_data,mimetype=mime_type or 'application/octat_stream',as_attachment=True,download_name=fdata[1])
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))    
@app.route('/deletefile/<fid>') 
def deletefile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)  
        cursor.execute('delete from file_data where fid=%s',[fid])
        mydb.commit()
        cursor.close()
        flash('file deleted successfully')
        return redirect(url_for('view_allfiles')) 
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin'))    
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from user where usermail=%s',[session.get('user')])   
        user_id=cursor.fetchone()  #[(1,)  (2,)] list of tuples
        cursor.execute('select notesid,title,description,created_at from notesdata where added_by=%s',[user_id[0]]) 
        userdata=cursor.fetchall()
        headings=['Notesid','Title','Description','Created_at']
        array=[list(i) for i in userdata] #list comprehension use chesi list of lists lo ki conversion
        array.insert(0,headings)
        return excel.make_response_from_array(array,"xlsx",file_name='notesexcel') 
    else:
        flash('pls login first') 
        return redirect(url_for('userlogin')) 
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        usersearch=request.form['search']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(usersearch):
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where usermail=%s',[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute('select notesid,title,description,created_at from notesdata where (notesid like %s or title like %s or description like %s or created_at like %s )and added_by=%s',[usersearch+'%',usersearch+'%',usersearch+'%',usersearch+'%',user_id[0]])
            resultsearch=cursor.fetchall()
            cursor.execute('select fid,filename,created_at from file_data where fid like %s or filename like %s or created_at like %s and added_by=%s',[usersearch+'%',usersearch+'%',usersearch+'%',user_id[0]])
            resultfile=cursor.fetchall()
            return render_template('dashboard.html',resultsearch=resultsearch,resultfile=resultfile)
        else:
            flash('no search found')  
            return render_template('dashboard.html')
    else:
        flash('pls login first')  
        return redirect(url_for('userlogin')) 
@app.route('/fgtpwd',methods=['GET','POST'])
def fgtpwd():
    if request.method=='POST':
        user_email=request.form['mail']
        print(user_email)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where usermail=%s',[user_email])
        count_usermail=cursor.fetchone() # account (1,) if not account (0,)
        if count_usermail[0]==1:
            subject='Reset link for password update Simple Notes management system'
            body=f"Use the given reset link for password update {url_for('confirmpwd',udata=endata(data=user_email),_external=True)}"
            send_mail(to=user_email,subject=subject,body=body)
            flash(f'Reset link has been sent given mail {user_email}')
            return redirect(url_for('fgtpwd'))
        elif count_usermail[0]==0:
            flash('User email not found pls check email')
            return redirect(url_for('register'))
    return render_template('forgotpassword.html')
@app.route('/confirmpwd/<udata>',methods=['GET','PUT'])
def confirmpwd(udata):
    if request.method=='PUT':
        npwd=request.get_json('password')['password']
        print(npwd)
        de_udata=dedata(udata)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update user set password=%s where usermail=%s',[npwd,de_udata])
        mydb.commit()
        cursor.close()
        flash('new password updated successfully')
        return 'ok'
    return render_template('npassword.html',udata=udata)       
if __name__=="__main__":
    app.run(debug=True,use_reloader=True)