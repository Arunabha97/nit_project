from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from students.models import Student
from teachers.models import Teacher

from . import addons
from .models import Temp_user


def login(request):
    if request.user.is_authenticated:
        return redirect(request.GET['next'] or 'index')
    else:
        if request.method == 'POST':
            user = auth.authenticate(username=request.POST['username'],password=request.POST['password'])
            if user is not None:
                auth.login(request, user)
                return redirect('index')
            else:
                error = "username or password invalid! Try signing up if not already!"
                if Temp_user.objects.filter(uname=request.POST['username']).exists():
                    error = "Please Varify your email before logging in!"
                
                return render(request, 'accounts/login.html',{"title":"login_error", 'error':error})
        else:
            return render(request, 'accounts/login.html', {"title":"log in"})


def  logout(request):
    if request.method == 'POST':
        auth.logout(request)
        return redirect('index')


def signup(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        if request.method == "POST":
            
            #-1. form validation
            #-2. check if the given user is a student or a teacher and has the valid email else STOP here.
            #-3. save data in local table (if not already there, in both user tables)
                #i. generate token
                #ii. send email
                #iii. show Email sent page
            #-4. if username exists, show an error page

            # validations:
            # =============

            error = ""
            try:
                that_stud = Student.objects.get(id=request.POST['username'])
                flag_stud = True
                saved_email = that_stud.email
            except:
                flag_stud = False

            if not flag_stud:
                try:
                    that_teach = Teacher.object.get(id=request.POST['username'])
                    flag_teach = True
                    saved_email = that_teach.email
                except:
                    flag_teach = False
                    error = "Unknown Id! Who are you exactly?? Go away..."
                    return render(request, 'accounts/signup.html', {'title':'signup error', 'error':error})
            
            # validate their email and if anything falls outs of place, DO NOT PROCEED further!!! 
            if flag_stud or flag_teach:
                if saved == request.POST['email']:
                    no_error = True
                else:
                    error = "Please give the Email that we know! This is critical to varify that its you!"
                    return render(request, 'accounts/signup.html', {'title':'signup error', 'error':error})
                    
            if request.POST["password1"] != request.POST["password2"]:
                error = "Passwords must match!"
            elif password1.isalpha():
                error = "mix in some numbers with the password"
            elif Temp_user.objects.filter(uname = request.POST["username"]).exists() or User.objects.filter(username = request.POST["username"]).exists():
                error = "You are already varified. Try Loging in!"
            elif Temp_user.objects.filter(email=request.POST["email"]).exists():
                msg = ["""
                The account is already signed in! Varify your email.
                <br /> Sometimes emails can take upto an hour to reach the destination.
                <br /> Please be patient! If this method fails repeatedly contact your mentor!!
                """]
            
                return message('signup error', msg, request)
            
            # main show starts from here:
            # ===========================
            else:
                token = addons.generate_url()
                Temp_user.objects.create(uname=request.POST['username'], password=make_password(request.POST['password1']), email=request.POST['email'], token=token)
                reciever = [request.POST["email"]]
                if addons.varification_mailto(reciever, token):
                    img = '<img src="' + addons.get_cute_image() + '" height="200px" width="200px" alt="a cute animal image">'
                    return render(request, 'accounts/resend.html', {'title':'email varifiaction','case':'first_time', 'token':token, 'cute_image': img})
                else:
                    responce = ["ERROR! mail not sent"] 
                return message('signed up', responce, request)
            if error:
                return render(request, 'accounts/signup.html', {'title':'signup error', 'error':error})
        
        else: # request.method is "GET"
            return render(request, 'accounts/signup.html', {'title':'signup'})


def activate(request):
    title = "email_varifiaction" # used to display as page title, nothing special!
    path = str(request.path)
    key = path.split("validate/", 1)[1]
    error = ""

    if Temp_user.objects.filter(token=key).exists():
        tuser = Temp_user.objects.get(token=key)
        
        if tuser.varify_time(timezone.now()): # checking whether the link is valid!
            # Adding to user
            user = User.objects.create_user(username=tuser.uname, password=tuser.password, email=tuser.email)
            user.password = tuser.password # Using this since django will re-hash the hashed password => Thus explicitely, re mentioning it!
            user.is_active = True
            user.save()

            # Deleting from Temp_user
            Temp_user.objects.filter(uname=tuser.uname).delete()
            login = '"' + reverse('login') + '"'
            msg = [
                "Welcome to snapshare!", 
                """Thanks for varifying your email! try <a href=""" + login + """>logging in! </a>"""
            ]

        # check if token is a reset token and do reset if yes
        # reset token starts with "reset"
        elif 'reset' in tuser.token:
            user = User.objects.get(username__exact=tuser.uname)
            user.set_password(tuser.password)
            user.save


        else:
            img = '<img src="' + addons.get_cute_image() + '" height="200px" width="200px" alt="a cute animal image">'
            return render(request, 'accounts/resend.html', {'title':"email error",'case':'expire', 'token':tuser.token, 'cute_image': img})
    else:
        title = "404"
        msg = "This way does not leads to mars!"
    return message(title, message, request)


def resend(request):
    if request.method == 'POST' and Temp_user.objects.filter(token=request.POST["token"]).exists():
        token = request.POST['token']
        tuser = Temp_user.objects.get(token=token)
        new_token = addons.generate_url()
        tuser.token = new_token
        tuser.save()
        reciver = [tuser.email]
        token = new_token
        if addons.varification_mailto(reciver, token):
            img = '<img src="' + addons.get_cute_image() + '" height="200px" width="200px" alt="a cute animal image">'
            return render(request, 'accounts/resend.html', {'title':'email varifiaction','case':'resend', 'token':new_token, 'cute_image': img})
        else:
            message = "ERROR! mail not sent"
    else:
        message = "Well, you have came a long way, to vain!"
    return message("404", message, request)


def reset(request):
    if request.method == "POST":
        error = ""  
        msg = ""    # error fails loudly
        flag = 0    #flag is used to fail silently
        id = request.POST['id']
        email = request.POST['email']
        name = request.POST['name']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if Student.objects.filter(id=id).exists() or Teacher.objects.filter(id=id).exists():
            if Student.objects.filter(id=id).exists():
                obj = Student.objects.get(id=id)
            else:
                obj = Teacher.objects.get(id=id)

            if not obj.is_varified:
                msg = "Frist varify your account"
            elif not obj.is_registered:
                msg = "Well, register first!"
            elif password1 != password2:
                error = 'Password must match'
            elif password1.isalpha():
                error = "mix in some numbers with the password"
            elif not obj.email == email:
                flag = 1
            elif not obj.name == name:
                flag = 1
        else:
            error = "Well, we don't know you!"

        if not flag and not error and not msg:
            reset_token = "reset"+addons.generate_url()
            if Temp_user.objects.filter(uname=obj.id).exists():
                Temp_user.objects.filter(uname=obj.id).update(password=password1, token=reset_token, time=timezone.now)
            else:
                Temp_user.objects.create(uname=obj.id, password=password1, email=obj.email, token=reset_token, time=timezone.now)
            reciever = [obj.email]
            if addons.varification_mailto(reciver, reset_token):
                msg = ["If you entered correct Name, Id and your registered email id", "expect to recive an email to reset password!"]
            else:
                msg = ["Error sending mail... Try again.", "If problem persists, contact your HOD!"]

        if msg:
            return message("reset_message", msg, request)
        elif error:
            return render(request, 'accounts/reset.html', {'title':'reset-error', 'error':error})

    else:
        return render(request, 'accounts/reset.html', {"title":"reset password"})


def message(title, mesg, request):
    _ = []
    if type(mesg) != type(_):
        mesg = [mesg]
    img = '<img src="' + addons.get_cute_image() + '" height="200px" width="200px" alt="a cute animal image">'
    return render(request, 'accounts/message.html', {'title':title, 'messages':msg, 'cute_img':img})