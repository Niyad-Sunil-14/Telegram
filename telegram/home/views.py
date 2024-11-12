from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . models import User,UserProfile,GroupMessage,ChatGroup
from . forms import UpdateImg,EditProfile,SetName,ChatmessageCreateForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def update_status(request):
    status = request.GET.get('status', 'False') == 'True'
    # Update the user's status in the database
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_profile.online = status
    user_profile.save()

    return JsonResponse({'success': True, 'user_status': status})

@login_required(login_url='login')
def home(request,chatroom_name='public-chat'):
    profile=User.objects.all()
    user=request.user
    profile_img=UpdateImg(instance=user)
    edit_profile=EditProfile(instance=user)
    set_name=SetName(instance=user)

    if request.method=="POST":
        if "search" in request.POST:
            search=request.POST['search']
            searched=User.objects.filter(username__icontains=search)
            profile=User.objects.all()
            return render(request,'home.html',{'search':search,'searched':searched,'profile':profile,'profile_img':profile_img,'edit_profile':edit_profile})
        
        elif "update_profile_img" in request.POST:
            profile_img=UpdateImg(request.POST,request.FILES,instance=user)
            if profile_img.is_valid():
                profile_img.save()
                return redirect('/')
            
        elif "edit_profile" in request.POST:
            edit_profile=EditProfile(request.POST,request.FILES,instance=user)
            if edit_profile.is_valid():
                edit_profile.save()
                return redirect('/')
            
        elif "set_name" in request.POST:
            set_name=SetName(request.POST,request.FILES,instance=user)
            if set_name.is_valid():
                set_name.save()
                return redirect('/')
                    

    context={
        'profile':profile,
        'profile_img':profile_img,
        'edit_profile':edit_profile,
        'set_name':set_name,
    }
    return render(request,'home.html',context)


def loginPage(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']

        user=authenticate(username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"Invalid username or password")
            return redirect('login')
    else:
        return render(request,'login.html')
    

def logoutPage(request):
    logout(request)
    return redirect('login')


def registerPage(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        conform_password=request.POST['conform_password']

        if password==conform_password:
            if User.objects.filter(username=username).exists():
                messages.error(request,"Username taken")
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.error(request,"Email alreay taken")
                return redirect('register')
            else:
                user=User.objects.create_user(username=username,
                                              email=email,
                                              password=password,
                                            )
                user.save()
                messages.success(request,"Registration Successfully completed...!")
                messages.info(request,"Now Login again")
                return redirect('register')
        else:
            messages.error(request,"Password not matching")
            return redirect('register') 

    return render(request,'register.html')

@login_required
def userRoom(request,pk):
    room=User.objects.get(pk=pk)
    profile=User.objects.all()
    user=request.user
    profile_img=UpdateImg(instance=user)
    edit_profile=EditProfile(instance=user)

    status = request.GET.get('status', 'False')
    online_live=UserProfile.objects.get(pk=pk)

    context={
        'room':room,
        'profile':profile,
        'profile_img':profile_img,
        'edit_profile':edit_profile,
        'user_status': status,
        'online_live':online_live,
        'chat_messages':chat_messages,
        'form':form
    }

    if request.method=="POST":
        if "search" in request.POST:
            search=request.POST['search']
            searched=User.objects.filter(username__icontains=search)
            profile=User.objects.all()
            return render(request,'home.html',{'search':search,'searched':searched,'profile':profile,'profile_img':profile_img,'edit_profile':edit_profile})

        elif "update_profile_img" in request.POST:
                profile_img=UpdateImg(request.POST,request.FILES,instance=user)
                if profile_img.is_valid():
                    profile_img.save()
                    return redirect('/')
                
        elif "edit_profile" in request.POST:
            edit_profile=EditProfile(request.POST,request.FILES,instance=user)
            if edit_profile.is_valid():
                edit_profile.save()
                return redirect('/')
        
    elif request.htmx:
        chat_group=get_object_or_404(ChatGroup,group_name="public-chat")
        chat_messages=chat_group.chat_messages.all()[:30]
        form=ChatmessageCreateForm() 
        if form.is_valid:
            message=form.save(commit=False)
            message.author=request.user
            message.group=chat_group
            message.save()
            context={
                'message':message,
                'user':request.user
            }
            return render(request,'room.html',context)
    
    return render(request,'room.html',context)


# # def room(request,room_name): 
#     room=User.objects.get(id=room_name)
#     profile=User.objects.all()
#     user=request.user
#     profile_img=UpdateImg(instance=user)
#     edit_profile=EditProfile(instance=user)

#     status = request.GET.get('status', 'False')
#     online_live=UserProfile.objects.get(id=room_name)

#     # msg_room=ChatRoom.objects.get(id=room_name)
#     # message=msg_room.message_set.all().order_by('created') 

#     context={
#         'room':room,
#         'profile':profile,
#         'profile_img':profile_img,
#         'edit_profile':edit_profile,
#         'user_status': status,
#         'online_live':online_live,
#         # 'message':message,
#         'room_name': room_name,
#     }

#     if request.method=="POST":
#         if "search" in request.POST:
#             search=request.POST['search']
#             searched=User.objects.filter(username__icontains=search)
#             profile=User.objects.all()
#             return render(request,'home.html',{'search':search,'searched':searched,'profile':profile,'profile_img':profile_img,'edit_profile':edit_profile})

#         elif "update_profile_img" in request.POST:
#                 profile_img=UpdateImg(request.POST,request.FILES,instance=user)
#                 if profile_img.is_valid():
#                     profile_img.save()
#                     return redirect('/')
                
#         elif "edit_profile" in request.POST:
#             edit_profile=EditProfile(request.POST,request.FILES,instance=user)
#             if edit_profile.is_valid():
#                 edit_profile.save()
#                 return redirect('/')
            
#         # elif "body" in request.POST:
#         #     # create_host_id=Room.objects.create(
#         #     #     sender=request.user,
#         #     #     reciver=User.objects.get(pk=pk)
#         #     # )
#         #     # message=Message.objects.create(
#         #     #     sender=request.user,
#         #     #     # reciver=Room.objects.get(pk=pk),
#         #     #     body=request.POST.get('body')
#         #     # )
            
#         #     return redirect('room',room_name)
        
#     return render(request, 'room.html',context)


@login_required
def chat_view(request):
    chat_group=get_object_or_404(ChatGroup,group_name="public-chat")
    chat_messages=chat_group.chat_messages.all()[:30]
    form=ChatmessageCreateForm()

    if request.htmx:
        form=ChatmessageCreateForm(request.POST)
        if form.is_valid:
            message= form.save(commit=False)
            message.author=request.user
            message.group=chat_group
            message.save()
            context={
                'message':message,
                'user':request.user
            }
            return render(request,'home/partials/chat_message_p.html',context=context)
        
    return render(request,"home/chat.html",{'chat_messages':chat_messages,'form':form})