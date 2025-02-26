from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . models import User,UserProfile,ChatGroup,GroupMessage
from . forms import UpdateImg,EditProfile,SetName,ChatmessageCreateForm,EditMessage
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.db.models import Prefetch
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


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
            chat_group=get_object_or_404(ChatGroup,group_name=chatroom_name)
            last_message = chat_group.chat_messages.order_by('-created').first()
            return render(request,'home.html',{'last_message':last_message,'search':search,'searched':searched,'profile':profile,'profile_img':profile_img,'edit_profile':edit_profile})
        
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
def chat_view(request,chatroom_name='public-chat'):
    profile=User.objects.all()
    user=request.user
    profile_img=UpdateImg(instance=user)
    edit_profile=EditProfile(instance=user)
    status = request.GET.get('status', 'False')

    chat_group=get_object_or_404(ChatGroup,group_name=chatroom_name)
    chat_messages=chat_group.chat_messages.all()[:30]
    last_message = chat_group.chat_messages.order_by('-created').first()
    form=ChatmessageCreateForm()

    other_user=None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user=member
                break

    online_live=UserProfile.objects.get(pk=other_user.id)

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
        
    if request.method=="POST":
        if "search" in request.POST:
            search=request.POST['search']
            searched=User.objects.filter(username__icontains=search)
            profile=User.objects.all()
            return render(request,'home.html',{'last_message':last_message,'search':search,'searched':searched,'profile':profile,'profile_img':profile_img,'edit_profile':edit_profile})

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
            
        # elif "edit_message" in request.POST:
        #     edit_message=EditMessage(request.POST,request.FILES,instance=user)
        #     if edit_message.is_valid():
        #         edit_message.save()
        #         return edit_message
        
    context={
        'chat_messages':chat_messages,
        'form':form,
        'other_user':other_user,
        'chatroom_name':chatroom_name,
        'profile':profile,
        'profile_img':profile_img,
        'edit_profile':edit_profile,
        'user_status': status,
        'online_live':online_live,
        'last_message':last_message,
    }
        
    return render(request,"home/chat.html",context)


@login_required
def get_or_create_chatroom(request,username):
    if request.user.username == username:
        return redirect('home')
    
    other_user=User.objects.get(username=username)
    my_chatrooms=request.user.chat_groups.filter(is_private=True)


    if my_chatrooms.exists():
        for chatroom in my_chatrooms:
            if other_user in chatroom.members.all():
                chatroom=chatroom
                break
            else:
                chatroom=ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user,request.user)
    else:
        chatroom=ChatGroup.objects.create(is_private=True)
        chatroom.members.add(other_user,request.user)

    return redirect('chatroom',chatroom.group_name)



def delete_message(request, message_id):
    if request.method == "POST":
        message = get_object_or_404(GroupMessage, id=message_id)
        message.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})



def update_message(request, message_id):
    message = get_object_or_404(GroupMessage, id=message_id) # user=request.user
    
    if request.method == "POST":
        new_body = request.POST.get("body")  # Changed from content to body
        if new_body:
            message.body = new_body
            message.save()
            return JsonResponse({"success": True})  # Return success JSON response
        return JsonResponse({"success": False, "error": "No body provided"})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


