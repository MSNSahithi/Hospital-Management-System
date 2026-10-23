from django.shortcuts import render, redirect
import requests

def signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        res = requests.post("http://127.0.0.1:8000/api/accounts/signup/", json={
            "username": username,
            "password": password,
            "role": role
        })

        if res.status_code == 201:
            return redirect("/login/")
        return render(request, "signup.html", {"error": res.json()})

    return render(request, "signup.html")


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        res = requests.post("http://127.0.0.1:8000/api/accounts/login/", json={
            "username": username,
            "password": password
        })

        if res.status_code == 200:
            token = res.json().get("token")
            request.session["token"] = token
            return redirect("/dashboard/")

        return render(request, "login.html", {"error": res.json()})

    return render(request, "login.html")


def dashboard_page(request):
    token = request.session.get("token")
    if not token:
        return redirect("/login/")
    return render(request, "dashboard.html", {"token": token})
