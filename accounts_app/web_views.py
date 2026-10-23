import requests
from django.shortcuts import render, redirect
from django.contrib import messages

API_BASE = "http://127.0.0.1:8000/api/accounts"


# ---------------- DOCTOR ----------------
def doctor_signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        payload = {"username": username, "password": password, "role": "DOCTOR"}

        res = requests.post(f"{API_BASE}/signup/", json=payload)

        if res.status_code == 201:
            messages.success(request, "Doctor Signup successful! Please login.")
            return redirect("/doctor/login/")
        else:
            messages.error(request, res.json())
            return redirect("/doctor/signup/")

    return render(request, "doctor_signup.html")


def doctor_login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        payload = {"username": username, "password": password}

        res = requests.post(f"{API_BASE}/login/", json=payload)

        if res.status_code == 200:
            data = res.json()
            request.session["token"] = data["token"]
            request.session["username"] = data["username"]
            request.session["role"] = data["role"]

            messages.success(request, "Doctor Login successful!")
            return redirect("/doctor/dashboard/")
        else:
            messages.error(request, res.json())
            return redirect("/doctor/login/")

    return render(request, "doctor_login.html")


# ---------------- PATIENT ----------------
def patient_signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        payload = {"username": username, "password": password, "role": "PATIENT"}

        res = requests.post(f"{API_BASE}/signup/", json=payload)

        if res.status_code == 201:
            messages.success(request, "Patient Signup successful! Please login.")
            return redirect("/patient/login/")
        else:
            messages.error(request, res.json())
            return redirect("/patient/signup/")

    return render(request, "patient_signup.html")


def patient_login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        payload = {"username": username, "password": password}

        res = requests.post(f"{API_BASE}/login/", json=payload)

        if res.status_code == 200:
            data = res.json()
            request.session["token"] = data["token"]
            request.session["username"] = data["username"]
            request.session["role"] = data["role"]

            messages.success(request, "Patient Login successful!")
            return redirect("/patient/dashboard/")
        else:
            messages.error(request, res.json())
            return redirect("/patient/login/")

    return render(request, "patient_login.html")
