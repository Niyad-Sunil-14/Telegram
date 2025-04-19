from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, UserProfile, ChatGroup, GroupMessage
from .forms import UpdateImg, EditProfile, SetName, ChatmessageCreateForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from asgiref.sync import async_to_sync
from django.db import models
from collections import defaultdict
from django.utils import timezone
from datetime import datetime
import pytz
from channels.layers import get_channel_layer

@csrf_exempt
@login_required
def update_status(request):
    status = request.GET.get('status', 'False') == 'True'
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_profile.online = status
    user_profile.save()

    channel_layer = get_channel_layer()
    chat_groups = request.user.chat_groups.all()
    for group in chat_groups:
        for member in group.members.all():
            if member != request.user:
                async_to_sync(channel_layer.group_send)(
                    f"user_{member.id}",
                    {
                        "type": "notify_status",
                        "user_id": request.user.id,
                        "username": request.user.username,
                        "online": status,
                    }
                )

    return JsonResponse({'success': True, 'user_status': status})

@login_required(login_url='login')
def home(request, chatroom_name='public-chat'):
    profile = User.objects.all()
    user = request.user
    profile_img = UpdateImg(instance=user)
    edit_profile = EditProfile(instance=user)
    set_name = SetName(instance=user)

    user_chat_groups_qs = ChatGroup.objects.filter(members=user).annotate(
        last_message_time=models.Max('chat_messages__created')
    ).order_by('-last_message_time')

    private_chats = defaultdict(list)
    recent_chats = []
    MIN_DATETIME = timezone.make_aware(datetime.min, pytz.utc)

    for group in user_chat_groups_qs:
        unread_count = group.get_unread_count(user)
        last_message = group.get_last_message()
        is_seen = last_message.is_seen if last_message and last_message.author == user else None
        if last_message:
            if last_message.image:
                if last_message.body:
                    last_message.body = f"🖼️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a photo"
                    else:
                        last_message.body = "Sent you a photo"
            elif last_message.audio:
                if last_message.body:
                    last_message.body = f"🎙️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a voice message"
                    else:
                        last_message.body = "Sent you a voice message"
        
        if group.is_private:
            other_member = group.members.exclude(id=user.id).first()
            if other_member:
                private_chats[other_member.id].append((group, unread_count, is_seen))
        else:
            recent_chats.append({
                'group_name': group.group_name,
                'is_private': False,
                'last_message': last_message,
                'display_name': group.group_name,
                'avatar_url': '/static/avatar.svg',
                'online_status': False,
                'unread_count': unread_count,
                'is_seen': is_seen,
            })

    for other_member_id, group_data in private_chats.items():
        other_member = User.objects.get(id=other_member_id)
        latest_group, unread_count, is_seen = max(group_data, key=lambda g: g[0].last_message_time or MIN_DATETIME)
        last_message = latest_group.get_last_message()
        if last_message:
            if last_message.image:
                if last_message.body:
                    last_message.body = f"🖼️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a photo"
                    else:
                        last_message.body = "Sent you a photo"
            elif last_message.audio:
                if last_message.body:
                    last_message.body = f"🎙️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a voice message"
                    else:
                        last_message.body = "Sent you a voice message"
        display_name = other_member.name if other_member.name else other_member.username
        recent_chats.append({
            'group_name': latest_group.group_name,
            'is_private': True,
            'last_message': last_message,
            'other_member': other_member,
            'display_name': display_name,
            'avatar_url': other_member.avatar.url,
            'online_status': other_member.userprofile.online,
            'unread_count': unread_count,
            'is_seen': is_seen,
        })
        
    recent_chats.sort(
        key=lambda x: x['last_message'].created if x['last_message'] else MIN_DATETIME,
        reverse=True
    )

    if request.method == "POST":
        if "search" in request.POST:
            search_query = request.POST['search'].strip()
            searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id) if search_query else None
            context = {
                'profile': profile,
                'profile_img': profile_img,
                'edit_profile': edit_profile,
                'set_name': set_name,
                'recent_chats': recent_chats,
                'search_query': search_query,
                'searched_users': searched_users,
                'chatroom_name': chatroom_name,
            }
            return render(request, 'home.html', context)
        
        elif "update_profile_img" in request.POST:
            profile_img = UpdateImg(request.POST, request.FILES, instance=user)
            if profile_img.is_valid():
                profile_img.save()
                return redirect('/')
            
        elif "edit_profile" in request.POST:
            edit_profile = EditProfile(request.POST, request.FILES, instance=user)
            if edit_profile.is_valid():
                edit_profile.save()
                return redirect('/')
            
        elif "set_name" in request.POST:
            set_name = SetName(request.POST, request.FILES, instance=user)
            if set_name.is_valid():
                set_name.save()
                return redirect('/')
                    
    context = {
        'profile': profile,
        'profile_img': profile_img,
        'edit_profile': edit_profile,
        'set_name': set_name,
        'recent_chats': recent_chats,
        'chatroom_name': chatroom_name,
    }
    return render(request, 'home.html', context)

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
def chat_view(request, chatroom_name='public-chat'):
    profile = User.objects.all()
    user = request.user
    profile_img = UpdateImg(instance=user)
    edit_profile = EditProfile(instance=user)
    status = request.GET.get('status', 'False')

    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()
    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    user_chat_groups_qs = ChatGroup.objects.filter(members=user).annotate(
        last_message_time=models.Max('chat_messages__created')
    ).order_by('-last_message_time')

    private_chats = defaultdict(list)
    recent_chats = []
    MIN_DATETIME = timezone.make_aware(datetime.min, pytz.utc)

    for group in user_chat_groups_qs:
        unread_count = group.get_unread_count(user)
        last_message = group.get_last_message()
        is_seen = last_message.is_seen if last_message and last_message.author == user else None
        if last_message:
            if last_message.image:
                if last_message.body:
                    last_message.body = f"🖼️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a photo"
                    else:
                        last_message.body = "Sent you a photo"
            elif last_message.audio:
                if last_message.body:
                    last_message.body = f"🎙️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a voice message"
                    else:
                        last_message.body = "Sent you a voice message"
        
        if group.is_private:
            other_member = group.members.exclude(id=user.id).first()
            if other_member:
                private_chats[other_member.id].append((group, unread_count, is_seen))
        else:
            recent_chats.append({
                'group_name': group.group_name,
                'is_private': False,
                'last_message': last_message,
                'display_name': group.group_name,
                'avatar_url': '/static/avatar.svg',
                'online_status': False,
                'unread_count': unread_count,
                'is_seen': is_seen,
            })

    for other_member_id, group_data in private_chats.items():
        other_member = User.objects.get(id=other_member_id)
        latest_group, unread_count, is_seen = max(group_data, key=lambda g: g[0].last_message_time or MIN_DATETIME)
        last_message = latest_group.get_last_message()
        if last_message:
            if last_message.image:
                if last_message.body:
                    last_message.body = f"🖼️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a photo"
                    else:
                        last_message.body = "Sent you a photo"
            elif last_message.audio:
                if last_message.body:
                    last_message.body = f"🎙️: {last_message.body}"
                else:
                    if last_message.author == user:
                        last_message.body = "You sent a voice message"
                    else:
                        last_message.body = "Sent you a voice message"
        display_name = other_member.name if other_member.name else other_member.username
        recent_chats.append({
            'group_name': latest_group.group_name,
            'is_private': True,
            'last_message': last_message,
            'other_member': other_member,
            'display_name': display_name,
            'avatar_url': other_member.avatar.url,
            'online_status': other_member.userprofile.online,
            'unread_count': unread_count,
            'is_seen': is_seen,
        })

    recent_chats.sort(
        key=lambda x: x['last_message'].created if x['last_message'] else MIN_DATETIME,
        reverse=True
    )

    online_live = UserProfile.objects.get(pk=other_user.id) if other_user else None

    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message': message,
                'user': request.user
            }
            return render(request, 'home/partials/chat_message_p.html', context=context)
        
    if request.method == "POST":
        if "search" in request.POST:
            search_query = request.POST['search'].strip()
            searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id) if search_query else None
            context = {
                'chat_messages': chat_messages,
                'form': form,
                'other_user': other_user,
                'chatroom_name': chatroom_name,
                'profile': profile,
                'profile_img': profile_img,
                'edit_profile': edit_profile,
                'user_status': status,
                'online_live': online_live,
                'recent_chats': recent_chats,
                'search_query': search_query,
                'searched_users': searched_users,
            }
            return render(request, 'home/chat.html', context)

        elif "update_profile_img" in request.POST:
            profile_img = UpdateImg(request.POST, request.FILES, instance=user)
            if profile_img.is_valid():
                profile_img.save()
                return redirect('/')
                
        elif "edit_profile" in request.POST:
            edit_profile = EditProfile(request.POST, request.FILES, instance=user)
            if edit_profile.is_valid():
                edit_profile.save()
                return redirect('/')
        
    context = {
        'chat_messages': chat_messages,
        'form': form,
        'other_user': other_user,
        'chatroom_name': chatroom_name,
        'profile': profile,
        'profile_img': profile_img,
        'edit_profile': edit_profile,
        'user_status': status,
        'online_live': online_live,
        'recent_chats': recent_chats,
    }
        
    return render(request, "home/chat.html", context)

@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username=username)
    my_chatrooms = request.user.chat_groups.filter(is_private=True)

    for chatroom in my_chatrooms:
        if other_user in chatroom.members.all() and chatroom.members.count() == 2:
            return redirect('chatroom', chatroom.group_name)

    chatroom = ChatGroup.objects.create(is_private=True)
    chatroom.members.add(other_user, request.user)
    return redirect('chatroom', chatroom.group_name)


def delete_message(request, message_id):
    if request.method == "POST":
        message = get_object_or_404(GroupMessage, id=message_id, author=request.user)
        return JsonResponse({"success": True, "message_id": message_id})
    return JsonResponse({"success": False})


def update_message(request, message_id):
    message = get_object_or_404(GroupMessage, id=message_id)
    
    if request.method == "POST":
        new_body = request.POST.get("body")
        if new_body:
            message.body = new_body
            message.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "No body provided"})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def upload_chat_image(request, chatroom_name):
    if request.method == "POST":
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        form = ChatmessageCreateForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                chatroom_name,
                {
                    'type': 'message_handler',
                    'message_id': message.id,
                }
            )
            return JsonResponse({'success': True, 'message_id': message.id})
        return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def upload_chat_audio(request, chatroom_name):
    if request.method == "POST":
        chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
        form = ChatmessageCreateForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                chatroom_name,
                {
                    'type': 'message_handler',
                    'message_id': message.id,
                }
            )
            return JsonResponse({'success': True, 'message_id': message.id})
        return JsonResponse({'success': False, 'error': form.errors.as_json()})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})