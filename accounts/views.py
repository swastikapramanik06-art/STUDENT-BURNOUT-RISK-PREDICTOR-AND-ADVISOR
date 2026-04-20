import os
import joblib
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings


ML_DIR = os.path.join(settings.BASE_DIR, 'ml_assets')

try:
    MODEL = joblib.load(os.path.join(ML_DIR, 'burnout_model_v3.pkl'))
    SCALER = joblib.load(os.path.join(ML_DIR, 'scaler_v3.pkl'))
    FEATURES = joblib.load(os.path.join(ML_DIR, 'features_v3.pkl'))
except Exception as e:
    print(f"Error loading ML assets: {e}")
    MODEL, SCALER, FEATURES = None, None, None


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


@login_required(login_url='login')
def dashboard_view(request):
    risk_result = None
    color_class = ""  
    solutions = []  

    if request.method == 'POST':
        try:
            # 1. Extraction of input parameters
            age = float(request.POST.get('age', 20))
            gender_str = request.POST.get('gender')
            gender = 1 if gender_str == 'male' else 0
            cgpa = float(request.POST.get('cgpa', 7.0))
            attendance = float(request.POST.get('attendance', 75))
            study_hrs = float(request.POST.get('study_hours', 0))
            sleep_hrs = float(request.POST.get('sleep_hours', 0))
            pressure_str = request.POST.get('pressure')
            pressure = 5 if pressure_str == 'yes' else 1
            anxiety_str = request.POST.get('anxiety')
            anxiety = 5 if anxiety_str == 'yes' else 1

            input_dict = {
                'age': age, 'gender': gender, 'course': 1, 'year': 3,
                'daily_study_hours': study_hrs, 'daily_sleep_hours': sleep_hrs,
                'screen_time_hours': 5.0, 'stress_level': pressure,
                'anxiety_score': anxiety, 'depression_score': 1,
                'academic_pressure_score': pressure, 'financial_stress_score': 2,
                'social_support_score': 3, 'physical_activity_hours': 1.0,
                'sleep_quality': 3, 'attendance_percentage': attendance,
                'cgpa': cgpa, 'internet_quality': 3
            }

            df = pd.DataFrame([input_dict])
            df = df[FEATURES]

            if MODEL and SCALER:
                
                scaled_data = SCALER.transform(df)
                prediction = MODEL.predict(scaled_data)[0]

                if prediction == 2:
                    risk_result, color_class = "High", "high-risk"
                    solutions.append("🔴 **Immediate Priority:** Model indicators suggest a critical strain level. Professional counseling is advised.")
                elif prediction == 1:
                    risk_result, color_class = "Moderate", "mod-risk"
                    solutions.append("🟡 **Advisory:** Analysis shows rising stress markers. Implementing a structured recovery day is recommended.")
                else:
                    risk_result, color_class = "Low", "low-risk"
                    solutions.append("🟢 **Optimal Balance:** Analytical engine confirms stable well-being. Continue your current routine.")

                if sleep_hrs < 6:
                    solutions.append("😴 **Restorative Sleep:** Current sleep patterns are below the cognitive threshold. Aim for 7+ hours.")
                
                if study_hrs > 9:
                    solutions.append("📚 **Strategic Recovery:** High concentration periods detected. Use the 50/10 rule to sustain focus.")
                
                if pressure_str == 'yes' or anxiety_str == 'yes':
                    solutions.append("🧘 **Wellness Pulse:** Analysis suggests high cortisol triggers. Practice 5 minutes of focused breathing.")

            else:
                messages.error(request, "Analytical Engine assets are currently unavailable.")

        except Exception as e:
            messages.error(request, f"Processing Error: {e}")

    return render(request, 'accounts/dashboard.html', {
        'risk_result': risk_result, 
        'color_class': color_class,
        'solutions': solutions  
    })
def logout_view(request):
    logout(request)
    return redirect('login')