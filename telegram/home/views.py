from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . models import User,UserProfile
from . forms import UpdateImg,EditProfile,SetName
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
def home(request):
    users=User.objects.all()
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
        'users':users,
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


def userRoom(request,pk):
    users=User.objects.all()
    room=User.objects.get(pk=pk)
    profile=User.objects.all()
    user=request.user
    profile_img=UpdateImg(instance=user)
    edit_profile=EditProfile(instance=user)

    status = request.GET.get('status', 'False')
    online_live=UserProfile.objects.get(id=pk)

    context={
        'users':users,
        'room':room,
        'profile':profile,
        'profile_img':profile_img,
        'edit_profile':edit_profile,
        'user_status': status,
        'online_live':online_live
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

    else:
        return render(request,'room.html',context)


