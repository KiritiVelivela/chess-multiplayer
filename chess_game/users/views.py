from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import UserCreationForm, LoginForm
from .models import UserStatus

# Create your views here.
def index(request):
    return render(request, 'index.html')

# signup page
def user_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

# login page
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)    
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

# logout page
def user_logout(request):
    user = request.user
    if hasattr(user, 'userstatus'):
        user.userstatus.is_logged_in = False
        user.userstatus.save()
    else:
        # Create a UserStatus if it doesn't exist
        UserStatus.objects.create(user=user, is_logged_in=False)
    
    logout(request)
    return redirect('login')