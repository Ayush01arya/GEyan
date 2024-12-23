from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.hashers import make_password
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import reportlab
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.contrib.auth.models import User
from .models import Reply  # Ensure this is present

from django.db.models import Count, Q
from .models import Profile,Complaint

from django.shortcuts import get_object_or_404,render, redirect
from django.http import HttpResponse
from .forms import UserRegisterForm,ProfileUpdateForm,UserProfileform,ComplaintForm,UserProfileUpdateform,statusupdate

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from datetime import datetime
#page loading.
def index(request):
    return render(request,"ComplaintMS/home.html")

def aboutus(request):
    return render(request,"ComplaintMS/aboutus.html")

def login(request):
    return render(request,"ComplaintMS/login.html")

def signin(request):
    return render(request,"ComplaintMS/signin.html")
def certificate(request):
    return render(request,"ComplaintMS/certificate.html")
#get the count of all the submitted complaints,solved,unsolved.

from django.http import JsonResponse
from .models import User  # Adjust based on your actual user model

import json
def check_user_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile_number = data.get('mobile_number')

            if User.objects.filter(mobile_number=mobile_number).exists():
                return JsonResponse({'is_registered': True})
            else:
                return JsonResponse({'is_registered': False})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def counter(request):
        total=Complaint.objects.all().count()
        unsolved=Complaint.objects.all().exclude(status='1').count()
        solved=Complaint.objects.all().exclude(Q(status='3') | Q(status='2')).count()
        dataset=Complaint.objects.values('Type_of_complaint').annotate(total=Count('status'),solved=Count('status', filter=Q(status='1')),
                  notsolved=Count('status', filter=Q(status='3')),inprogress=Count('status',filter=Q(status='2'))).order_by('Type_of_complaint')
        args={'total':total,'unsolved':unsolved,'solved':solved,'dataset':dataset,}
        return render(request,"ComplaintMS/counter.html",args)

#changepassword for grievancemember.
def change_password_g(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.add_message(request,messages.SUCCESS, f'Your password was successfully updated!')
            return redirect('change_password_g')
        else:
            messages.add_message(request,messages.WARNING, f'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'ComplaintMS/change_password_g.html', {
        'form': form
    })
    return render(request,"ComplaintMS/change_password_g.html")

#registration page.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        profile_form=UserProfileform(request.POST)
        if form.is_valid() and profile_form.is_valid() :

            new_user=form.save()
            profile=profile_form.save(commit=False)
            if profile.user_id is None:
                profile.user_id=new_user.id
            profile.save()
            messages.add_message(request,messages.SUCCESS, f' Registered Successfully ')
            return redirect('/login/')
    else:
        form = UserRegisterForm()
        profile_form=UserProfileform()

    context={'form': form,'profile_form':profile_form }
    return render(request, 'ComplaintMS/register.html',context )
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.contrib.auth.models import User

def login_user_via_otp(request, mobile_number):
    try:
        user = User.objects.get(profile__mobile_number=mobile_number)
        # Authenticate the user (since OTP is being used, password is bypassed)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)  # Log the user in
        return redirect('/dashboard/')
    except User.DoesNotExist:
        return redirect('/signin/')  # Redirect to sign-in if user not found

def login_redirect(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Check the user's profile type and redirect accordingly
        if request.user.profile.type_user == 'student':
            return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/counter/')
    else:
        # If the user is not authenticated, redirect to the login page
        return HttpResponseRedirect('/login/')

@login_required
def dashboard(request):
        
    if request.method == 'POST':
        p_form=ProfileUpdateForm(request.POST,instance=request.user)
        profile_update_form=UserProfileUpdateform(request.POST,instance=request.user.profile)
        if p_form.is_valid() and profile_update_form.is_valid():
                user=p_form.save()
                profile=profile_update_form.save(commit=False)
                profile.user=user
                profile.save()
                messages.add_message(request,messages.SUCCESS, f'Updated Successfully')
                return render(request,'ComplaintMS/dashboard.html',)
    else:
        p_form=ProfileUpdateForm(instance=request.user)
        profile_update_form=UserProfileUpdateform(instance=request.user.profile)
    context={
        'p_form':p_form,
        'profile_update_form':profile_update_form
        }
    return render(request, 'ComplaintMS/dashboard.html',context)

#change password for user.

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.add_message(request,messages.SUCCESS, f'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.add_message(request,messages.WARNING, f'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'ComplaintMS/change_password.html', {
        'form': form
    })





#complaints handling and submission section.
@login_required
def complaints(request):
  
    if request.method == 'POST':
           
        
        complaint_form=ComplaintForm(request.POST)
        if complaint_form.is_valid():
            
          
               instance=complaint_form.save(commit=False)
               instance.user=request.user
        #        mail=request.user.email
        #        print(mail)
        #        send_mail('Hi Complaint has been Received', 'Thank you for letting us know of your concern, Have a Cookie while we explore into this matter.  Dont Reply to this mail', 'testerpython13@gmail.com', [mail],fail_silently=False)
               instance.save()
               
               messages.add_message(request,messages.SUCCESS, f'Your Question has been registered!')
               return render(request,'ComplaintMS/comptotal.html',)
    else:
        
        complaint_form=ComplaintForm(request.POST)
    context={'complaint_form':complaint_form,}
    return render(request,'ComplaintMS/comptotal.html',context)
        

@login_required
def list(request):
    c=Complaint.objects.filter(user=request.user).exclude(status='1')
    result=Complaint.objects.filter(user=request.user).exclude(Q(status='3') | Q(status='2'))
    #c=Complaint.objects.all()
    args={'c':c,'result':result}
    return render(request,'ComplaintMS/Complaints.html',args)
@login_required
def slist(request):
    result=Complaint.objects.filter(user=request.user).exclude(Q(status='3') | Q(status='2'))
    #c=Complaint.objects.all()
    args={'result':result}
    return render(request,'ComplaintMS/solvedcomplaint.html',args)

@login_required
def allcomplaints(request):
      
        
        c=Complaint.objects.all().exclude(status='1')
        comp=request.GET.get("search")
        drop=request.GET.get("drop")

        if drop:
                c=c.filter(Q(Type_of_complaint__icontains=drop))
        if comp:
                c=c.filter(Q(Type_of_complaint__icontains=comp)|Q(Description__icontains=comp)|Q(Subject__icontains=comp))
        if request.method=='POST':
                cid=request.POST.get('cid2')
                uid=request.POST.get('uid')
                print(uid)
                project = Complaint.objects.get(id=cid)
                
                forms=statusupdate(request.POST,instance=project)
                if forms.is_valid():
                        
                        obj=forms.save(commit=False)
                        mail = User.objects.filter(id=uid)
                        for i in mail:
                                m=i.email
                       
                      
                        print(m)
                        # send_mail('Hi, Complaint has been Resolved ', 'Thanks for letting us know of your concern, Hope we have solved your issue. Dont Reply to this mail', 'testerpython13@gmail.com', [m],fail_silently=False)
                        obj.save()
                        messages.add_message(request,messages.SUCCESS, f'The complaint has been updated!')
                        return HttpResponseRedirect(reverse('allcomplaints'))
                else:
                        return render(request,'ComplaintMS/AllComplaints.html')
                 #testing

        else:
                forms=statusupdate()
        #c=Complaint.objects.all().exclude(status='1')
           
        args={'c':c,'forms':forms,'comp':comp}
        return render(request,'ComplaintMS/allcomplaints.html',args)

@login_required
def solved(request):
        
        cid=request.POST.get('cid2')
        c=Complaint.objects.all().exclude(Q(status='3') | Q(status='2'))
        comp=request.GET.get("search")
        drop=request.GET.get("drop")

        if drop:
                c=c.filter(Q(Type_of_complaint__icontains=drop))
        if comp:
               
                c=c.filter(Q(Type_of_complaint__icontains=comp)|Q(Description__icontains=comp)|Q(Subject__icontains=comp))
        if request.method=='POST':
                cid=request.POST.get('cid2')
                print(cid)
                project = Complaint.objects.get(id=cid)
                forms=statusupdate(request.POST,instance=project)
                if forms.is_valid():
                        
                        obj=forms.save(commit=False)
                        obj.save()
                        messages.add_message(request,messages.SUCCESS, f'The complaint has been updated!')
                        return HttpResponseRedirect(reverse('solved'))
                else:
                        return render(request,'ComplaintMS/solved.html')
                 #testing

        else:
                forms=statusupdate()
        #c=Complaint.objects.all().exclude(Q(status='3') | Q(status='2'))
        
        args={'c':c,'forms':forms,'comp':comp}
        return render(request,'ComplaintMS/solved.html',args)

#allcomplaints pdf viewer.
def pdf_viewer(request):
    detail_string={}
    #detailname={}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=Complaint_id.pdf'
    p = canvas.Canvas(response,pagesize=A4)
    
    cid=request.POST.get('cid')
    uid=request.POST.get('uid')
    #print(cid)
    
    details = Complaint.objects.filter(id=cid).values('Description')
    name = Complaint.objects.filter(id=cid).values('user_id')
    '''Branch = Complaint.objects.filter(id=cid).values('Branch')'''
    Subject = Complaint.objects.filter(id=cid).values('Subject')
    Type = Complaint.objects.filter(id=cid).values('Type_of_complaint')
    Issuedate = Complaint.objects.filter(id=cid).values('Time')
    #date_format1 = "%Y-%m-%d %H:%M:%S.%f%z"
   
    
    for val in details:
            detail_string=("{}".format(val['Description']))
    for val in name:
           detailname=("User: {}".format(val['user_id']))
    '''for val in Branch:
            detailbranch=("Branch: {}".format(val['Branch']))'''
    for val in Subject:
            detailsubject=("Subject: {}".format(val['Subject']))
    for val in Type:
            detailtype=("{}".format(val['Type_of_complaint']))
            
    for val in Issuedate:
            ptime=("{}".format(val['Time']))
            detailtime=("Time of Issue/ Time of Solved: {}".format(val['Time']))
    #detail_string = u", ".join(("Desc={}".format(val['Description'])) for val in details) 
    date_format = "%Y-%m-%d"
    a = datetime.strptime(str(datetime.now().date()), date_format)
    b = datetime.strptime(str(ptime), date_format)
    delta = a - b
    print(b)
    print(a)
    print (delta.days )       
    if detailtype=='1':
            detailtype="Type of Questions: Question 1"
    if detailtype=='3':
            detailtype="Type of Questions: Question 0"
    if detailtype=='2':
            detailtype="Type of Questions: Question 2"
    if detailtype=='4':
            detailtype="Type of Questions: Question 3"
    if detailtype=='5':
            detailtype="Type of Questions: Question 4"

    p.drawString(25, 770,"Report:")
    p.drawString(30, 750,detailname)
    ''' p.drawString(30, 730,detailbranch)'''
    p.drawString(30, 710,detailtype)
    p.drawString(30, 690,detailtime)
    p.drawString(30, 670,detailsubject)
    p.drawString(30, 650,"Description:")
    p.drawString(30, 630,detail_string)

    p.showPage()
    p.save()
    return response


def reply_to_complaint(request):
    if request.method == 'POST':
        complaint_id = request.POST.get('cid2')
        reply_message = request.POST.get(
            'reply_message')  # Assuming you have a field in your form named 'reply_message'

        # Fetch the complaint by ID and update the response
        complaint = Complaint.objects.get(id=complaint_id)
        complaint.reply = reply_message  # Assuming you have a 'reply' field in your Complaint model
        complaint.status = 2  # Mark as replied (example)
        complaint.save()

        messages.success(request, 'Reply sent successfully.')
        return redirect('allcomplaints')  # Redirect to all complaints page

    return redirect('allcomplaints')
#complaints pdf view.
@login_required
def pdf_view(request):
    detail_string={}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=complaint_id.pdf'
    
    p = canvas.Canvas(response,pagesize=A4)
    cid=request.POST.get('cid')
    #print(cid)
    details = Complaint.objects.filter(id=cid).values('Description')
    name = User.objects.filter(username=request.user.username).values('username')
    #Branch = Complaint.objects.filter(id=cid).values('Branch')
    Subject = Complaint.objects.filter(id=cid).values('Subject')
    Type = Complaint.objects.filter(id=cid).values('Type_of_complaint')
    Issuedate = Complaint.objects.filter(id=cid).values('Time')

    for val in details:
            detail_string=("{}".format(val['Description']))
    for val in name:
            detailname=("User: {}".format(val['username']))
    #for val in Branch:
            #detailbranch=("Branch: {}".format(val['Branch']))
    for val in Subject:
            detailsubject=("Subject: {}".format(val['Subject']))
    for val in Type:
            detailtype=("{}".format(val['Type_of_complaint']))
            
    for val in Issuedate:
            detailtime=("Time of Issue: {}".format(val['Time']))
    #detail_string = u", ".join(("Desc={}".format(val['Description'])) for val in details) 

    if detailtype=='1':
            detailtype="Type of Question : Question1"
    if detailtype=='3':
            detailtype="Type of Question: Question2"
    if detailtype=='2':
            detailtype="Type of Question: Question3"
    if detailtype=='4':
            detailtype="Type of Question: Question4"
    if detailtype=='5':
            detailtype="Type of Question: Question5"

    p.drawString(25, 770,"Report:")
    p.drawString(30, 750,detailname)
    #p.drawString(30, 730,detailbranch)
    p.drawString(30, 710,detailtype)
    p.drawString(30, 690,detailtime)
    p.drawString(30, 670,detailsubject)
    p.drawString(30, 650,"Description:")
    p.drawString(30, 630,detail_string)

    p.showPage()
    p.save()
    return response

from django.shortcuts import render, redirect, get_object_or_404
from .models import Complaint
from .forms import ReplyForm


@login_required
def reply_to_complaint(request, complaint_id):
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, id=complaint_id)
        reply_text = request.POST.get('reply_text')
        # Create a reply
        Reply.objects.create(complaint=complaint, user=request.user, reply_text=reply_text)

        # Set the complaint status to solved
        complaint.status = 1  # Assuming 1 means solved
        complaint.save()

        # Optionally add a success message
        messages.success(request, "Your reply has been submitted and the complaint is marked as solved.")
        return redirect('all_complaints')
from django.shortcuts import render
from .models import Complaint

def all_complaints_view(request):
    complaints = Complaint.objects.all()  # Retrieve complaints
    return render(request, 'AllComplaints.html', {'complaints': complaints})
