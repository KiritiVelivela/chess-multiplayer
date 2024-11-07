from django.shortcuts import render, redirect
from app1.models import Board
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from app1.forms import SudokuForm, JoinForm, LoginForm


# Create your views here.
@login_required(login_url='/login/')
def home(request):
    room_name = None
    page_data = { "rows": [], "sudoku_form": SudokuForm }
    # If there are is no Board model data, or if the user pressed the new game
    # button, create a new game in the Board model
    if (Board.objects.filter(user=request.user).count() == 0) or \
    (request.method == 'POST' and 'new_game' in request.POST):
        newGame(request)
    elif (request.method == 'POST' and 'room_name' in request.POST):
        room_name = request.POST["room_name"]
        print("handled POST, room_name='{}'".format(room_name))
    elif (request.method == 'POST'):
        sudoku_form = SudokuForm(request.POST)
        if (sudoku_form.is_valid()):
            location = sudoku_form.cleaned_data["location"]
            value = sudoku_form.cleaned_data["value"]
            # Force replacement
            Board.objects.filter(user=request.user, location=location).delete()
            Board(user=request.user, location=location, value=value).save()
        else:
            page_data["sudoku_form"] = sudoku_form

    if (not room_name):
        room_name = request.COOKIES.get("room_name")
        print("Got room_name '{}' from COOKIES".format(room_name))

    if (room_name):
        page_data["room_name"] = room_name
        print("Setting page_data room_name to '{}'".format(room_name))

    # Populate page_data from board model
    for row in range(1, 10):
        row_data = {}
        for col in range(1, 10):
            id = "r{}c{}".format(row, col)
            try:
                record = Board.objects.get(user=request.user, location=id)
                row_data[id] = record.value
            except Board.DoesNotExist:
                row_data[id] = 0
        page_data.get("rows").append(row_data)
    response = render(request, 'app1/home.html', page_data)
    if (room_name):
            response.set_cookie("room_name", room_name)
    return response

def rules(request):
    return render(request, 'app1/rules.html')

def about(request):
    return render(request, 'app1/about.html')

def newGame(request):
    page_data = {
        "rows": [
        {"r1c1": 6, "r1c2": 7, "r1c3": 0, "r1c4": 0, "r1c5": 4, "r1c6": 8, "r1c7": 0, "r1c8": 1, "r1c9": 0},
        {"r2c1": 3, "r2c2": 5, "r2c3": 0, "r2c4": 0, "r2c5": 0, "r2c6": 1, "r2c7": 0, "r2c8": 4, "r2c9": 7},
        {"r3c1": 0, "r3c2": 1, "r3c3": 0, "r3c4": 7, "r3c5": 2, "r3c6": 0, "r3c7": 6, "r3c8": 8, "r3c9": 0},
        {"r4c1": 8, "r4c2": 0, "r4c3": 3, "r4c4": 0, "r4c5": 0, "r4c6": 0, "r4c7": 1, "r4c8": 6, "r4c9": 9},
        {"r5c1": 0, "r5c2": 0, "r5c3": 7, "r5c4": 9, "r5c5": 1, "r5c6": 0, "r5c7": 8, "r5c8": 3, "r5c9": 0},
        {"r6c1": 0, "r6c2": 9, "r6c3": 6, "r6c4": 4, "r6c5": 8, "r6c6": 3, "r6c7": 0, "r6c8": 0, "r6c9": 0},
        {"r7c1": 0, "r7c2": 0, "r7c3": 9, "r7c4": 1, "r7c5": 0, "r7c6": 4, "r7c7": 3, "r7c8": 0, "r7c9": 8},
        {"r8c1": 4, "r8c2": 8, "r8c3": 1, "r8c4": 0, "r8c5": 0, "r8c6": 0, "r8c7": 7, "r8c8": 0, "r8c9": 6},
        {"r9c1": 7, "r9c2": 0, "r9c3": 0, "r9c4": 8, "r9c5": 6, "r9c6": 2, "r9c7": 0, "r9c8": 0, "r9c9": 1}
        ]
    } 
    # Delete all board model objects (records)
    Board.objects.filter(user=request.user).delete()
 
    # Populate board model objects from page_data
    for row in page_data.get("rows"):
        for location, value in row.items():
            Board(user=request.user, location=location, value=value).save()

def join(request):
    if (request.method == "POST"):
        join_form = JoinForm(request.POST)
        if (join_form.is_valid()):
            # Save form data to DB
            user = join_form.save()
            # Encrypt the password
            user.set_password(user.password)
            # Save encrypted password to DB
            user.save()
            # Success! Redirect to home page.
            return redirect("/")
        else:
            # Form invalid, print errors to console
            page_data = { "join_form": join_form }
            return render(request, 'app1/join.html', page_data)
    else:
        join_form = JoinForm()
        page_data = { "join_form": join_form }
        return render(request, 'app1/join.html', page_data)

def user_login(request):
    if (request.method == 'POST'):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            # First get the username and password supplied
            username = login_form.cleaned_data["username"]
            password = login_form.cleaned_data["password"]
            # Django's built-in authentication function:
            user = authenticate(username=username, password=password)
            # If we have a user
            if user:
                #Check it the account is active
                if user.is_active:
                    # Log the user in.
                    login(request,user)
                    # Send the user back to homepage
                    return redirect("/")
                else:
                    # If account is not active:
                    return HttpResponse("Your account is not active.")
            else:
                print("Someone tried to login and failed.")
                print("They used username: {} and password: {}".format(username,password))
                return render(request, 'app1/login.html', {"login_form": LoginForm})
    else:
        #Nothing has been provided for username or password.
        return render(request, 'app1/login.html', {"login_form": LoginForm})

@login_required(login_url='/login/')    
def user_logout(request):
    # Log out the user.
    logout(request)
    # Return to homepage.
    return redirect("/")
